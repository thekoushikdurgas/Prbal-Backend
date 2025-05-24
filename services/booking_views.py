from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Booking, Payment, ChatMessage, Bid, ServiceRequest, Review
from .serializers import (
    BookingListSerializer,
    BookingDetailSerializer,
    BookingStatusUpdateSerializer,
    BookingCustomerConfirmSerializer,
    PaymentSerializer,
    ChatMessageSerializer,
    ReviewListSerializer,
    ReviewDetailSerializer,
    ProviderResponseSerializer
)
from .permissions import IsServiceProvider, IsCustomer
import stripe
from django.conf import settings
from datetime import timedelta

stripe.api_key = settings.STRIPE_SECRET_KEY

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    ordering_fields = ['scheduled_datetime', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'PROVIDER':
            return Booking.objects.filter(provider=user)
        return Booking.objects.filter(customer=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return BookingListSerializer
        elif self.action == 'update_status':
            return BookingStatusUpdateSerializer
        elif self.action == 'confirm_completion':
            return BookingCustomerConfirmSerializer
        return BookingDetailSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """List bookings for the current user"""
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update booking status (provider only)"""
        booking = self.get_object()
        if booking.provider != request.user:
            return Response(
                {"detail": "Only the provider can update the booking status."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BookingStatusUpdateSerializer(
            booking,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            with transaction.atomic():
                booking = serializer.save()
                
                # If provider marks as completed, set their confirmation
                if serializer.validated_data['status'] == 'completed':
                    booking.provider_completion_confirmation = timezone.now()
                    booking.save()
                    
                    # Check if customer already confirmed or grace period passed
                    if booking.customer_completion_confirmation or (
                        timezone.now() - booking.provider_completion_confirmation
                        > booking.completion_grace_period
                    ):
                        self._initiate_payment_release(booking)
                
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def confirm_completion(self, request, pk=None):
        """Confirm service completion (customer only)"""
        booking = self.get_object()
        if booking.customer != request.user:
            return Response(
                {"detail": "Only the customer can confirm completion."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if booking.status not in ['completed', 'payment_pending']:
            return Response(
                {"detail": "Booking must be marked as completed by the provider first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            booking.customer_completion_confirmation = timezone.now()
            booking.save()
            
            # If provider has also confirmed, release payment
            if booking.provider_completion_confirmation:
                self._initiate_payment_release(booking)
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        user = request.user
        
        # Validate cancellation is allowed
        if booking.status not in ['scheduled', 'in_progress']:
            return Response(
                {"detail": "This booking cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate user is involved in the booking
        if user not in [booking.customer, booking.provider]:
            return Response(
                {"detail": "You are not authorized to cancel this booking."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason', '')
        
        with transaction.atomic():
            # Update booking status
            booking.status = (
                'cancelled_by_customer' if user == booking.customer
                else 'cancelled_by_provider'
            )
            booking.cancellation_reason = reason
            booking.cancelled_by = user
            booking.cancelled_at = timezone.now()
            booking.save()
            
            # Handle payment refund if needed
            payment = booking.payments.filter(
                status__in=['pending', 'held_in_escrow']
            ).first()
            
            if payment and payment.stripe_charge_id:
                try:
                    refund = stripe.Refund.create(
                        payment_intent=payment.stripe_charge_id
                    )
                    payment.status = 'refunded'
                    payment.refund_id = refund.id
                    payment.save()
                except stripe.error.StripeError as e:
                    # Log the error but don't prevent cancellation
                    print(f"Stripe refund error: {str(e)}")
                    payment.status = 'failed'
                    payment.error_message = str(e)
                    payment.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)

    def _initiate_payment_release(self, booking):
        """Internal method to initiate payment release from escrow"""
        try:
            payment = booking.payments.filter(status='held_in_escrow').first()
            if not payment or not payment.stripe_charge_id:
                raise ValueError("No valid payment found in escrow")
            
            # Calculate provider's amount (agreed price minus platform fee)
            provider_amount = int((booking.agreed_price - booking.platform_fee) * 100)  # Convert to cents
            
            # Create a transfer to the provider's connected account
            transfer = stripe.Transfer.create(
                amount=provider_amount,
                currency='usd',
                destination=booking.provider.stripe_account_id,
                transfer_group=f'BOOKING_{booking.id}',
                source_transaction=payment.stripe_charge_id
            )
            
            with transaction.atomic():
                # Update payment status
                payment.status = 'released_to_provider'
                payment.save()
                
                # Update booking status
                booking.status = 'paid'
                booking.save()
                
        except (stripe.error.StripeError, ValueError) as e:
            # Log the error and update statuses
            print(f"Payment release error: {str(e)}")
            if payment:
                payment.status = 'failed'
                payment.error_message = str(e)
                payment.save()
            booking.status = 'payment_failed'
            booking.save()
            raise

    @transaction.atomic
    def create(self, serializer):
        """Create a new booking and initiate payment"""
        booking = serializer.save()
        
        # Create payment record
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.agreed_price,
            status='pending'
        )
        
        try:
            # Create Stripe PaymentIntent for escrow
            intent = stripe.PaymentIntent.create(
                amount=int(booking.agreed_price * 100),  # Convert to cents
                currency='usd',
                payment_method_types=['card'],
                transfer_group=f'BOOKING_{booking.id}',
                metadata={
                    'booking_id': booking.id,
                    'customer_id': booking.customer.id,
                    'provider_id': booking.provider.id
                }
            )
            
            payment.stripe_charge_id = intent.id
            payment.save()
            
            # Return the booking data along with the client secret
            response_data = serializer.data
            response_data['client_secret'] = intent.client_secret
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except stripe.error.StripeError as e:
            # Rollback the booking creation
            booking.delete()
            return Response(
                {"detail": "Payment initialization failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        booking_id = self.kwargs.get('booking_pk')
        if not booking_id:
            return ChatMessage.objects.none()
        
        booking = get_object_or_404(Booking, id=booking_id)
        user = self.request.user
        
        # Only allow access if user is the customer or provider of the booking
        if user != booking.customer and user != booking.provider:
            return ChatMessage.objects.none()
            
        return ChatMessage.objects.filter(booking_id=booking_id)

    def perform_create(self, serializer):
        booking_id = self.kwargs.get('booking_pk')
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Verify user is either customer or provider
        user = self.request.user
        if user != booking.customer and user != booking.provider:
            raise permissions.PermissionDenied(
                "You must be the customer or provider of this booking to send messages."
            )
            
        serializer.save(sender=user, booking_id=booking_id)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None, booking_pk=None):
        """Mark a message as read"""
        message = self.get_object()
        user = request.user
        
        # Only mark as read if user is the recipient
        if (message.sender == booking.customer and user == booking.provider) or \
           (message.sender == booking.provider and user == booking.customer):
            message.read_at = timezone.now()
            message.save()
            return Response({'status': 'message marked as read'})
        return Response(
            {"detail": "You cannot mark this message as read."},
            status=status.HTTP_403_FORBIDDEN
        ) 
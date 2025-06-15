from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from django.utils import timezone
from django.db import transaction

from .models import Payment, PaymentGatewayAccount, Payout
from .serializers import (
    PaymentListSerializer,
    PaymentDetailSerializer,
    PaymentInitiateSerializer,
    PaymentConfirmSerializer,
    PaymentGatewayAccountSerializer,
    PayoutListSerializer,
    PayoutDetailSerializer,
    PayoutRequestSerializer,
    EarningsSummarySerializer
)
from .permissions import IsPaymentParticipant, IsPaymentPayer, IsPayoutProvider
from bookings.models import Booking
from decimal import Decimal

class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for payments - allows listing, retrieving, and managing payments.
    Implements role-based filtering and permissions based on user role and participation.
    """
    queryset = Payment.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['booking', 'status', 'payment_method']
    search_fields = ['notes']
    ordering_fields = ['created_at', 'amount', 'payment_date']
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is not authenticated, return nothing
        if not user.is_authenticated:
            return Payment.objects.none()
            
        # Staff can see all payments
        if user.is_staff:
            return Payment.objects.all()
            
        # Users see payments they're part of (as payer or payee)
        return Payment.objects.filter(Q(payer=user) | Q(payee=user))
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailSerializer
        elif self.action == 'initiate':
            return PaymentInitiateSerializer
        elif self.action == 'confirm':
            return PaymentConfirmSerializer
        return PaymentListSerializer
    
    def get_permissions(self):
        if self.action in ['retrieve']:
            # Only participants can view payment details
            return [permissions.IsAuthenticated(), IsPaymentParticipant()]
        elif self.action in ['initiate', 'confirm']:
            # Only the payer can initiate or confirm a payment
            return [permissions.IsAuthenticated()]
        # List view is filtered by user role in get_queryset
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """
        Initiate a payment for a booking.
        This will create a Payment object with 'pending' status and potentially
        communicate with a payment gateway to get a payment intent/client secret.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            booking_id = serializer.validated_data['booking_id']
            booking = Booking.objects.get(id=booking_id)
            
            # Create a pending payment
            payment = Payment.objects.create(
                booking=booking,
                payer=request.user,  # Customer initiating the payment
                payee=booking.provider,  # Service provider receiving the payment
                amount=booking.amount,
                payment_method=serializer.validated_data['payment_method'],
                status='pending',
                # Calculate platform fee (e.g., 10% of the amount)
                platform_fee=Decimal(booking.amount) * Decimal('0.10')
            )
            
            # In a real implementation, you would now communicate with a payment gateway
            # to create a payment intent/client secret and return it to the client
            
            # For this example, we'll just return a placeholder
            payment_intent = {
                'id': str(payment.id),
                'client_secret': f"pi_mock_{payment.id}_secret",
                'amount': float(payment.amount),
                'currency': 'usd',
                'status': 'requires_payment_method'
            }
            
            return Response({
                'payment_id': payment.id,
                'payment_intent': payment_intent,
                'message': "Payment initiated successfully. Complete the payment process on the frontend."
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def confirm(self, request):
        """
        Confirm a payment after the user completes the action on the frontend.
        This will update the Payment status and the associated Booking status.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            payment_id = serializer.validated_data['payment_id']
            payment = Payment.objects.get(id=payment_id)
            
            # In a real implementation, you would verify the payment with the payment gateway
            # and update the payment status accordingly
            
            # For this example, we'll just update the payment status to 'completed'
            with transaction.atomic():
                # Update payment status
                payment.status = 'completed'
                payment.transaction_id = serializer.validated_data.get('transaction_id', f"txn_mock_{payment.id}")
                payment.save()
                
                # Update booking status to 'confirmed' if it's pending
                booking = payment.booking
                if booking.status == 'pending':
                    booking.status = 'confirmed'
                    booking.save()
                
                # Create a notification for the provider about the payment
                from notifications.utils import send_notification
                provider = booking.provider
                send_notification(
                    recipient=provider,
                    notification_type='payment_received',
                    title='Payment Received',
                    message=f'You received a payment of {payment.amount} for booking {booking.service.title}',
                    content_object=payment,
                    action_url=f'/provider/bookings/{booking.id}/'
                )
                
                # Also notify the customer about the confirmed booking
                send_notification(
                    recipient=booking.customer,
                    notification_type='booking_status_updated',
                    title='Booking Confirmed',
                    message=f'Your booking for {booking.service.title} has been confirmed',
                    content_object=booking,
                    action_url=f'/bookings/{booking.id}/'
                )
            
            return Response({
                'payment_id': payment.id,
                'status': payment.status,
                'booking_id': booking.id,
                'booking_status': booking.status,
                'message': "Payment confirmed successfully."
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get payment history for the authenticated user.
        Can be filtered by role parameter (payer/payee).
        """
        role = request.query_params.get('role')
        
        queryset = self.get_queryset()
        if role == 'payer':
            queryset = queryset.filter(payer=request.user)
        elif role == 'payee':
            queryset = queryset.filter(payee=request.user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PaymentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PaymentListSerializer(queryset, many=True)
        return Response(serializer.data)

class PaymentGatewayAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for payment gateway accounts - allows listing, creating, and managing accounts.
    """
    serializer_class = PaymentGatewayAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PaymentGatewayAccount.objects.filter(user=self.request.user)

class PayoutViewSet(viewsets.ModelViewSet):
    """
    ViewSet for payouts - allows listing, retrieving, and requesting payouts.
    """
    queryset = Payout.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'processed_at', 'amount']
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is not authenticated, return nothing
        if not user.is_authenticated:
            return Payout.objects.none()
            
        # Staff can see all payouts
        if user.is_staff:
            return Payout.objects.all()
            
        # Providers see their own payouts
        return Payout.objects.filter(provider=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PayoutDetailSerializer
        elif self.action == 'request_payout':
            return PayoutRequestSerializer
        return PayoutListSerializer
    
    def get_permissions(self):
        if self.action in ['retrieve']:
            # Only the provider can view their payout details
            return [permissions.IsAuthenticated(), IsPayoutProvider()]
        # List view is filtered by user role in get_queryset
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['post'], url_path='request')
    def request_payout(self, request):
        """
        Request a payout of available earnings.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Get the payment account
            account_id = serializer.validated_data['payment_account_id']
            account = PaymentGatewayAccount.objects.get(id=account_id)
            
            # Get the requested amount
            amount = serializer.validated_data['amount']
            
            # Calculate transaction fee (e.g., 2% of the amount)
            transaction_fee = Decimal(amount) * Decimal('0.02')
            net_amount = amount - transaction_fee
            
            # Create a pending payout
            payout = Payout.objects.create(
                provider=request.user,
                payment_account=account,
                amount=amount,
                transaction_fee=transaction_fee,
                net_amount=net_amount,
                status='pending'
            )
            
            # In a real implementation, you would now communicate with a payment gateway
            # to initiate the payout process
            
            # Create a notification for the provider about the payout request
            from notifications.utils import send_notification
            send_notification(
                recipient=request.user,
                notification_type='payout_processed',
                title='Payout Request Received',
                message=f'Your payout request for {amount} has been submitted and is being processed.',
                content_object=payout,
                action_url=f'/provider/payouts/{payout.id}/'
            )
            
            # Also notify admin about the payout request (if needed)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            for admin in User.objects.filter(is_staff=True, is_active=True):
                send_notification(
                    recipient=admin,
                    notification_type='payout_processed',
                    title='Payout Request Received',
                    message=f'Provider {request.user.get_full_name() or request.user.username} has requested a payout of {amount}.',
                    content_object=payout,
                    action_url=f'/admin/payments/payout/{payout.id}/change/'
                )
            
            return Response({
                'payout_id': payout.id,
                'amount': float(payout.amount),
                'net_amount': float(payout.net_amount),
                'status': payout.status,
                'message': "Payout request submitted successfully."
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def earnings(self, request):
        """
        Get a summary of the provider's earnings and payout history.
        """
        user = request.user
        
        # Get completed payments where user is the payee
        completed_payments = Payment.objects.filter(
            payee=user,
            status='completed'
        )
        
        # Calculate total earnings
        total_earnings = completed_payments.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # Calculate pending earnings (from bookings that are not yet completed)
        pending_bookings = Booking.objects.filter(
            provider=user,
            status__in=['confirmed', 'in_progress']
        )
        pending_earnings = pending_bookings.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # Calculate completed payouts
        completed_payouts = Payout.objects.filter(
            provider=user,
            status='completed'
        )
        completed_payout_amount = completed_payouts.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # Calculate pending payouts
        pending_payouts = Payout.objects.filter(
            provider=user,
            status__in=['pending', 'processing']
        )
        pending_payout_amount = pending_payouts.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # Calculate available for payout
        available_for_payout = total_earnings - completed_payout_amount - pending_payout_amount
        
        # Serialize the data
        serializer = EarningsSummarySerializer(data={
            'total_earnings': total_earnings,
            'pending_earnings': pending_earnings,
            'available_for_payout': available_for_payout,
            'completed_payouts': completed_payout_amount,
            'pending_payouts': pending_payout_amount
        })
        serializer.is_valid()
        
        return Response(serializer.data, status=status.HTTP_200_OK)

from django.shortcuts import render
from django.db.models import Q
from django.db import transaction # Added for atomic transactions
from rest_framework import viewsets, generics, permissions, filters, status
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import ServiceCategory, Service, ServiceRequest, Bid, Booking, Payment, Review, Payout, Notification # Added Booking, Payment, Review, Payout, Notification
from .serializers import (
    ServiceCategorySerializer,
    ServiceSerializer,
    ServiceRequestListSerializer,
    ServiceRequestDetailSerializer,
    BidListSerializer,
    BidDetailSerializer,
    BidActionSerializer,
    AIPriceSuggestionSerializer,
    BookingListSerializer,
    BookingDetailSerializer,
    BookingStatusUpdateSerializer,
    BookingCustomerConfirmSerializer,
    ChatMessageSerializer,
    PaymentSerializer,
    ReviewListSerializer,
    ReviewDetailSerializer,
    ProviderResponseSerializer,
    PayoutSerializer,
    PayoutInitiateSerializer,
    NotificationSerializer
)
from users.models import User # Ensure User model is imported if not already
from .permissions import IsServiceProvider, IsCustomer
import stripe
from django.conf import settings
# from django.db.models.deletion import ProtectedError
# from django.db.models.fields import DateTimeField
# from django.db.models.fields.related import ForeignKey
# from django.db.models.fields.related import ManyToManyField
# from django.db.models.fields.related import OneToOneField
# from django.db.models.fields.related import ManyToOneRel
# from django.db.models.fields.related import OneToOneRel
# from django.db.models.fields.related import ManyToManyRel

# Create your views here.

class ServiceCategoryViewSet(viewsets.ModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsServiceProvider]
    filterset_fields = ['category', 'service_area', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'hourly_rate']

    def get_queryset(self):
        if self.action == 'list':
            return Service.objects.filter(is_active=True)
        return Service.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsServiceProvider()]

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user)

class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceRequestDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'category', 'location']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'desired_datetime']
    queryset = ServiceRequest.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'CUSTOMER':
            # Customers can see their own requests
            return ServiceRequest.objects.filter(customer=user)
        else:
            # Providers can see open requests in their service areas and categories
            provider_services = user.services.all()
            service_areas = provider_services.values_list('service_area', flat=True)
            categories = provider_services.values_list('category', flat=True)
            
            return ServiceRequest.objects.filter(
                Q(status=ServiceRequest.Status.OPEN) &
                (Q(location__in=service_areas) | Q(category__in=categories))
            )

    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceRequestListSerializer
        return ServiceRequestDetailSerializer

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """List requests created by the current user"""
        if request.user.user_type != 'CUSTOMER':
            return Response(
                {"detail": "Only customers can view their requests."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = ServiceRequest.objects.filter(customer=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = ServiceRequestListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ServiceRequestListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        """List requests available for bidding"""
        if request.user.user_type != 'PROVIDER':
            return Response(
                {"detail": "Only service providers can view available requests."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        provider_services = request.user.services.all()
        service_areas = provider_services.values_list('service_area', flat=True)
        categories = provider_services.values_list('category', flat=True)
        
        queryset = ServiceRequest.objects.filter(
            status=ServiceRequest.Status.OPEN,
            desired_datetime__gt=timezone.now(),
        ).filter(
            Q(location__in=service_areas) | Q(category__in=categories)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ServiceRequestListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ServiceRequestListSerializer(queryset, many=True)
        return Response(serializer.data)

class BidViewSet(viewsets.ModelViewSet):
    serializer_class = BidDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'amount']

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'CUSTOMER':
            # Customers can see bids on their requests
            return Bid.objects.filter(service_request__customer=user)
        else:
            # Providers can see their own bids
            return Bid.objects.filter(provider=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return BidListSerializer
        return BidDetailSerializer

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """List bids submitted by the current user"""
        if request.user.user_type != 'PROVIDER':
            return Response(
                {"detail": "Only service providers can view their bids."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = Bid.objects.filter(provider=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = BidListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = BidListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a bid and create a booking"""
        bid = self.get_object()
        
        if request.user != bid.service_request.customer:
            return Response(
                {"detail": "Only the request owner can accept bids."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if bid.service_request.status != ServiceRequest.Status.OPEN:
            return Response(
                {"detail": "Can only accept bids on open requests."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Update bid status
            bid.status = Bid.Status.ACCEPTED
            bid.save()
            
            # Update request status
            service_request = bid.service_request
            service_request.status = ServiceRequest.Status.ASSIGNED
            service_request.save()
            
            # Reject other bids
            service_request.bids.exclude(id=bid.id).update(
                status=Bid.Status.REJECTED
            )
            
            # Create booking
            booking = Booking.objects.create(
                service_request=service_request,
                accepted_bid=bid,
                customer=request.user,
                provider=bid.provider,
                service=service_request.service,
                scheduled_datetime=bid.proposed_datetime,
                duration_minutes=bid.estimated_hours * 60,
                location_address=service_request.location,
                agreed_price=bid.amount,
                status='scheduled'
            )
            
            try:
                # Create payment record and initiate Stripe payment
                payment = Payment.objects.create(
                    booking=booking,
                    amount=booking.agreed_price,
                    status='pending'
                )
                
                # Create Stripe PaymentIntent for escrow
                stripe.api_key = settings.STRIPE_SECRET_KEY
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
                
                response_data = BidDetailSerializer(bid).data
                response_data['booking'] = {
                    'id': booking.id,
                    'client_secret': intent.client_secret
                }
                return Response(response_data)
                
            except stripe.error.StripeError as e:
                # If payment setup fails, roll back the booking creation
                booking.delete()
                return Response(
                    {"detail": "Payment initialization failed."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a bid"""
        bid = self.get_object()
        
        if request.user != bid.service_request.customer:
            return Response(
                {"detail": "Only the request owner can reject bids."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        bid.status = Bid.Status.REJECTED
        bid.save()
        
        return Response(BidDetailSerializer(bid).data)

    @action(detail=False, methods=['post'])
    def suggest_price(self, request):
        """Get AI-suggested price for a service request"""
        serializer = AIPriceSuggestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # TODO: Implement AI price suggestion logic
        # For now, return a dummy response
        return Response({
            "suggested_price": 100.00,
            "confidence": 0.85,
            "factors": [
                "Similar service history",
                "Location",
                "Time of request"
            ]
        })

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rating']
    ordering_fields = ['created_at', 'rating']

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'PROVIDER':
            return Review.objects.filter(provider=user)
        return Review.objects.filter(customer=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ReviewListSerializer
        elif self.action == 'respond':
            return ProviderResponseSerializer
        return ReviewDetailSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """List reviews for the current user"""
        user = request.user
        if user.user_type == 'PROVIDER':
            queryset = Review.objects.filter(provider=user)
        else:
            queryset = Review.objects.filter(customer=user)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ReviewListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ReviewListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Add a provider response to a review"""
        review = self.get_object()
        
        # Ensure only the provider can respond
        if request.user != review.provider:
            return Response(
                {"detail": "Only the provider can respond to this review."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProviderResponseSerializer(
            review,
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def provider(self, request):
        """List reviews for a specific provider"""
        provider_id = request.query_params.get('provider_id')
        if not provider_id:
            return Response(
                {"detail": "provider_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            provider = User.objects.get(id=provider_id, user_type='PROVIDER')
        except User.DoesNotExist:
            return Response(
                {"detail": "Provider not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        queryset = Review.objects.filter(provider=provider)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = ReviewListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ReviewListSerializer(queryset, many=True)
        return Response(serializer.data)

class PayoutViewSet(viewsets.ModelViewSet):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated, IsServiceProvider]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    ordering_fields = ['initiated_at', 'amount']

    def get_queryset(self):
        return Payout.objects.filter(provider=self.request.user)

    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initiate a new payout request"""
        serializer = PayoutInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        amount = serializer.validated_data['amount']

        try:
            with transaction.atomic():
                # Create payout record
                payout = Payout.objects.create(
                    provider=request.user,
                    amount=amount
                )

                # Initiate Stripe payout
                stripe_payout = stripe.Payout.create(
                    amount=int(amount * 100),  # Convert to cents
                    currency='usd',
                    destination=request.user.stripe_account_id,  # Assuming this field exists
                )

                # Update payout record with Stripe ID
                payout.stripe_payout_id = stripe_payout.id
                payout.status = Payout.Status.IN_TRANSIT
                payout.save()

                return Response(
                    PayoutSerializer(payout).data,
                    status=status.HTTP_201_CREATED
                )

        except stripe.error.StripeError as e:
            # Handle Stripe errors
            if 'payout' in locals():
                payout.status = Payout.Status.FAILED
                payout.error_message = str(e)
                payout.save()
                return Response(
                    PayoutSerializer(payout).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Handle other errors
            if 'payout' in locals():
                payout.status = Payout.Status.FAILED
                payout.error_message = str(e)
                payout.save()
                return Response(
                    PayoutSerializer(payout).data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_read', 'type']
    ordering_fields = ['created_at']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        # Only allow updating is_read status
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'success'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    ordering_fields = ['initiated_at', 'amount']

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'PROVIDER':
            return Payment.objects.filter(booking__provider=user)
        return Payment.objects.filter(booking__customer=user)

    def perform_create(self, serializer):
        serializer.save(initiated_by=self.request.user)

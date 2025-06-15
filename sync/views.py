from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from services.models import Service
from bids.models import Bid
from bids.serializers import BidCreateSerializer
from bookings.models import Booking
from bookings.serializers import BookingCreateDirectSerializer
from messagings.models import Message
from messagings.serializers import MessageCreateSerializer

from .serializers import (
    UserSyncSerializer,
    ServiceSyncSerializer,
    SyncUploadSerializer
)

class UserProfileSyncView(generics.RetrieveAPIView):
    """
    API endpoint to download the user's profile for offline use.
    
    Returns a detailed version of the user profile with all necessary
    information for offline functionality.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSyncSerializer
    
    def get_object(self):
        return self.request.user

class ServicesSyncView(generics.ListAPIView):
    """
    API endpoint to download available services for offline browsing.
    
    Returns a list of services with all necessary information for
    offline display and functionality. Can be filtered by category,
    location, and other parameters.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServiceSyncSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'price', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Service.objects.filter(status='active')
        
        # Apply filters if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__id=category)
            
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
            
        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))
        
        # Allow limiting the number of services for faster syncing
        limit = self.request.query_params.get('limit')
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
            
        return queryset
    
    def list(self, response, *args, **kwargs):
        # Get the standard response
        response = super().list(self.request, *args, **kwargs)
        
        # Add sync metadata
        response.data['sync_timestamp'] = timezone.now()
        response.data['expires_after'] = getattr(settings, 'SYNC_DATA_EXPIRES_HOURS', 24)
        
        return response

class SyncUploadView(APIView):
    """
    API endpoint to upload offline changes to the backend.
    
    Accepts data created or modified while the user was offline,
    and processes it in a transaction to ensure data integrity.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = SyncUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Process uploaded data
        processed_data = {
            'bids': [],
            'bookings': [],
            'messages': [],
            'errors': []
        }
        
        # Process bids
        for bid_data in serializer.validated_data.get('bids', []):
            # Add the current user as the bidder
            bid_data['provider'] = request.user.id
            
            bid_serializer = BidCreateSerializer(data=bid_data, context={'request': request})
            if bid_serializer.is_valid():
                bid = bid_serializer.save()
                processed_data['bids'].append({
                    'id': str(bid.id),
                    'client_temp_id': bid_data.get('client_temp_id'),
                    'status': 'created'
                })
            else:
                processed_data['errors'].append({
                    'type': 'bid',
                    'data': bid_data,
                    'errors': bid_serializer.errors
                })
        
        # Process bookings
        for booking_data in serializer.validated_data.get('bookings', []):
            # Add the current user as the customer
            booking_data['customer'] = request.user.id
            
            booking_serializer = BookingCreateDirectSerializer(data=booking_data, context={'request': request})
            if booking_serializer.is_valid():
                booking = booking_serializer.save()
                processed_data['bookings'].append({
                    'id': str(booking.id),
                    'client_temp_id': booking_data.get('client_temp_id'),
                    'status': 'created'
                })
            else:
                processed_data['errors'].append({
                    'type': 'booking',
                    'data': booking_data,
                    'errors': booking_serializer.errors
                })
        
        # Process messages
        for message_data in serializer.validated_data.get('messages', []):
            # Add the current user as the sender
            message_serializer = MessageCreateSerializer(data=message_data, context={'request': request})
            if message_serializer.is_valid():
                message = message_serializer.save(sender=request.user)
                processed_data['messages'].append({
                    'id': str(message.id),
                    'client_temp_id': message_data.get('client_temp_id'),
                    'status': 'sent'
                })
            else:
                processed_data['errors'].append({
                    'type': 'message',
                    'data': message_data,
                    'errors': message_serializer.errors
                })
        
        # Return processing results
        return Response({
            'success': len(processed_data['errors']) == 0,
            'processed': processed_data,
            'sync_timestamp': timezone.now()
        })

from rest_framework import serializers
from .models import Booking
from bids.models import Bid
from services.models import Service
from users.serializers import PublicUserProfileSerializer
from services.serializers import ServiceDetailSerializer
from datetime import datetime
"""
Serializers for calendar integration functionality.
"""
from rest_framework import serializers
from .models import Booking
from .sync import CALENDAR_PROVIDERS
class BookingListSerializer(serializers.ModelSerializer):
    """Serializer for listing bookings with minimal details"""
    service_title = serializers.CharField(source='service.title', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    provider_name = serializers.CharField(source='provider.get_full_name', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'service', 'service_title', 'customer', 'customer_name',
            'provider', 'provider_name', 'booking_date', 'amount', 'status',
            'created_at'
        ]
        read_only_fields = fields

class BookingDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed booking view with all relationships"""
    service = ServiceDetailSerializer(read_only=True)
    customer = PublicUserProfileSerializer(read_only=True)
    provider = PublicUserProfileSerializer(read_only=True)
    cancelled_by_name = serializers.CharField(source='cancelled_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'service', 'customer', 'provider', 'bid',
            'booking_date', 'completion_date', 'amount', 'status',
            'requirements', 'notes', 
            # Rescheduling fields
            'is_rescheduled', 'original_booking_date', 'rescheduled_count', 'rescheduled_reason',
            # Cancellation fields
            'cancellation_reason', 'cancelled_by', 'cancelled_by_name', 'cancellation_date',
            # Calendar sync
            'calendar_event_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

class BookingCreateFromBidSerializer(serializers.ModelSerializer):
    """Serializer for creating a booking from an accepted bid"""
    bid_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'bid_id', 'booking_date', 'requirements'
        ]
        read_only_fields = ['id']
    
    def validate_bid_id(self, value):
        """Ensure the bid exists and is still pending"""
        try:
            bid = Bid.objects.get(id=value)
            if bid.status != 'pending':
                raise serializers.ValidationError(f"This bid is already {bid.status}.")
            return value
        except Bid.DoesNotExist:
            raise serializers.ValidationError("Bid not found.")
    
    def create(self, validated_data):
        bid_id = validated_data.pop('bid_id')
        bid = Bid.objects.get(id=bid_id)
        
        # Create booking from bid data
        booking = Booking.objects.create(
            service=bid.service,
            customer=self.context['request'].user,  # Customer accepts the bid
            provider=bid.provider,
            bid=bid,
            booking_date=validated_data.get('booking_date'),
            amount=bid.amount,
            requirements=validated_data.get('requirements', ''),
            status='pending'
        )
        
        # Update bid status
        bid.status = 'accepted'
        bid.save()
        
        return booking

class BookingCreateDirectSerializer(serializers.ModelSerializer):
    """Serializer for creating a booking directly (without a bid)"""
    
    class Meta:
        model = Booking
        fields = [
            'id', 'service', 'booking_date', 'amount',
            'requirements', 'notes'
        ]
        read_only_fields = ['id']
    
    def validate_service(self, value):
        """Ensure the service exists and is active"""
        if not Service.objects.filter(id=value.id, status='active').exists():
            raise serializers.ValidationError("This service is not active or does not exist.")
        return value
    
    def create(self, validated_data):
        # Create booking directly
        service = validated_data.get('service')
        booking = Booking.objects.create(
            service=service,
            customer=self.context['request'].user,  # Customer creates the booking
            provider=service.provider,
            booking_date=validated_data.get('booking_date'),
            amount=validated_data.get('amount'),
            requirements=validated_data.get('requirements', ''),
            notes=validated_data.get('notes', ''),
            status='pending'
        )
        
        return booking

class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating the status of a booking"""
    
    class Meta:
        model = Booking
        fields = ['id', 'status', 'notes']
        read_only_fields = ['id']
    
    def validate_status(self, value):
        """Ensure the status transition is valid"""
        current_status = self.instance.status
        user = self.context['request'].user
        
        # Define valid status transitions
        valid_transitions = {
            # Provider transitions
            'provider': {
                'confirmed': ['in_progress', 'disputed'],
                'in_progress': ['completed', 'disputed'],
                'pending': ['disputed']
            },
            # Customer transitions
            'customer': {
                'pending': ['confirmed', 'cancelled', 'disputed'],
                'confirmed': ['cancelled', 'disputed'],
                'in_progress': ['disputed']
            }
        }
        
        # Determine user role in this booking
        role = None
        if user == self.instance.provider:
            role = 'provider'
        elif user == self.instance.customer:
            role = 'customer'
        else:
            raise serializers.ValidationError("You are not a participant in this booking.")
        
        # Check if transition is valid
        allowed_transitions = valid_transitions.get(role, {}).get(current_status, [])
        if value not in allowed_transitions:
            raise serializers.ValidationError(
                f"Cannot change status from '{current_status}' to '{value}' as {role}."
            )
            
        # For completion, check if the booking date has passed
        if value == 'completed' and self.instance.booking_date > datetime.now():
            raise serializers.ValidationError(
                "Cannot mark as completed before the booking date."
            )
            
        return value
    
    def update(self, instance, validated_data):
        # Update the completion date if status is being set to completed
        if validated_data.get('status') == 'completed' and instance.status != 'completed':
            validated_data['completion_date'] = datetime.now()
            
        return super().update(instance, validated_data)


class BookingRescheduleSerializer(serializers.ModelSerializer):
    """Serializer for rescheduling a booking"""
    
    class Meta:
        model = Booking
        fields = ['id', 'booking_date', 'rescheduled_reason']
        read_only_fields = ['id']
    
    def validate_booking_date(self, value):
        """Ensure the new booking date is in the future"""
        if value <= datetime.now():
            raise serializers.ValidationError("New booking date must be in the future.")
            
        return value
    
    def validate(self, data):
        """Additional validation for the booking state"""
        if self.instance.status in ['completed', 'cancelled', 'disputed']:
            raise serializers.ValidationError(f"Cannot reschedule a booking with status '{self.instance.status}'.")
            
        # Ensure reason is provided
        if not data.get('rescheduled_reason'):
            raise serializers.ValidationError("Please provide a reason for rescheduling.")
            
        return data
    
    def update(self, instance, validated_data):
        # Store original booking date if this is the first reschedule
        if not instance.is_rescheduled:
            instance.original_booking_date = instance.booking_date
            
        # Update booking
        instance.booking_date = validated_data.get('booking_date')
        instance.rescheduled_reason = validated_data.get('rescheduled_reason')
        instance.is_rescheduled = True
        instance.rescheduled_count += 1
        
        # If booking was cancelled due to reschedule, update the status back to confirmed/pending
        if instance.status == 'cancelled' and instance.cancellation_reason == 'rescheduled':
            instance.status = 'confirmed' if instance.status == 'cancelled' else instance.status
            
        instance.save()
        return instance


class CalendarSyncSerializer(serializers.Serializer):
    """
    Serializer for calendar synchronization requests.
    """
    booking_id = serializers.UUIDField(required=True)
    provider = serializers.CharField(required=True)
    auth_token = serializers.CharField(required=True, write_only=True)
    calendar_id = serializers.CharField(required=False)
    create_reminder = serializers.BooleanField(default=True)
    reminder_minutes = serializers.IntegerField(default=30, min_value=5, max_value=1440)
    
    def validate_provider(self, value):
        """Validate that the provider is supported."""
        
        if value not in CALENDAR_PROVIDERS:
            raise serializers.ValidationError(
                f"Unsupported calendar provider. Must be one of: {', '.join(CALENDAR_PROVIDERS.keys())}"
            )
        return value
    
    def validate_booking_id(self, value):
        """Validate that the booking exists and user has access to it."""
        try:
            booking = Booking.objects.get(id=value)
            
            # Check if the user has access to this booking
            request = self.context.get('request')
            if request and request.user and request.user.is_authenticated:
                user = request.user
                if booking.customer != user and booking.provider != user:
                    raise serializers.ValidationError("You don't have permission to sync this booking.")
            
            return value
            
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")

class CalendarEventResponseSerializer(serializers.Serializer):
    """
    Serializer for calendar event response data.
    """
    success = serializers.BooleanField()
    provider = serializers.CharField()
    event_id = serializers.CharField()
    booking_id = serializers.UUIDField()
    sync_time = serializers.DateTimeField()
    error = serializers.CharField(required=False)

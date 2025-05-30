"""
Serializers for calendar integration functionality.
"""
from rest_framework import serializers
from .models import Booking

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
        from .calendar_sync import CALENDAR_PROVIDERS
        
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

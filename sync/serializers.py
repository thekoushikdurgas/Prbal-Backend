from rest_framework import serializers
from users.models import User
from services.models import Service, ServiceCategory
from bids.models import Bid
from bookings.models import Booking

class UserSyncSerializer(serializers.ModelSerializer):
    """Serializer for downloading user profile for offline use"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 
            'user_type', 'phone_number', 'profile_picture', 'bio', 
            'location', 'is_verified', 'rating', 'balance',
            'date_joined', 'last_login'
        ]
        read_only_fields = fields

class ServiceCategorySyncSerializer(serializers.ModelSerializer):
    """Serializer for service categories in offline mode"""
    class Meta:
        model = ServiceCategory
        fields = [
            'id', 'name', 'description', 'icon', 'is_active'
        ]
        read_only_fields = fields

class ServiceProviderSerializer(serializers.ModelSerializer):
    """Simplified provider serializer for services"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'profile_picture', 'rating', 'is_verified'
        ]
        read_only_fields = fields

class ServiceSyncSerializer(serializers.ModelSerializer):
    """Serializer for downloading services for offline browsing"""
    provider = ServiceProviderSerializer(read_only=True)
    category = ServiceCategorySyncSerializer(read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'provider', 'category', 'title', 'description',
            'price', 'location', 'image', 'status', 'is_featured',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

class SyncUploadSerializer(serializers.Serializer):
    """Serializer for handling offline changes upload"""
    bids = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        default=[]
    )
    bookings = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        default=[]
    )
    messages = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        default=[]
    )
    timestamp = serializers.DateTimeField(required=True)

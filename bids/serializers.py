from rest_framework import serializers
from .models import Bid
from services.models import Service
from users.serializers import PublicUserProfileSerializer
from services.serializers import ServiceDetailSerializer

class BidListSerializer(serializers.ModelSerializer):
    """Serializer for listing bids with minimal provider details"""
    provider = PublicUserProfileSerializer(read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            'id', 'service', 'service_title', 'provider', 'amount', 
            'estimated_delivery_time', 'status', 'is_ai_suggested',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'provider', 'status', 'is_ai_suggested', 'created_at', 'updated_at']

class BidDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed bid view with provider and service details"""
    provider = PublicUserProfileSerializer(read_only=True)
    service = ServiceDetailSerializer(read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            'id', 'service', 'provider', 'amount', 'description',
            'estimated_delivery_time', 'status', 'is_ai_suggested',
            'ai_suggestion_id', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

class BidCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new bid"""
    is_ai_suggested = serializers.BooleanField(default=False, required=False)
    ai_suggestion_id = serializers.UUIDField(required=False, allow_null=True)
    
    class Meta:
        model = Bid
        fields = [
            'id', 'service', 'amount', 'description', 'estimated_delivery_time',
            'is_ai_suggested', 'ai_suggestion_id'
        ]
        read_only_fields = ['id']
    
    def validate_service(self, value):
        """Ensure the service exists and is active"""
        if not Service.objects.filter(id=value.id, status='active').exists():
            raise serializers.ValidationError("This service is not active or does not exist.")
        
        # Ensure provider is not bidding on their own service
        if value.provider == self.context['request'].user:
            raise serializers.ValidationError("You cannot bid on your own service.")
            
        return value

class BidUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an existing bid"""
    
    class Meta:
        model = Bid
        fields = [
            'id', 'amount', 'description', 'estimated_delivery_time'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Additional validation for bid updates"""
        # Only allow updates if the bid is still pending
        if self.instance and self.instance.status != 'pending':
            raise serializers.ValidationError(
                "This bid can no longer be updated as its status is not 'pending'."
            )
        return data

class BidStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating the status of a bid"""
    
    class Meta:
        model = Bid
        fields = ['id', 'status']
        read_only_fields = ['id']
    
    def validate_status(self, value):
        """Ensure the status transition is valid"""
        if self.instance.status != 'pending':
            raise serializers.ValidationError(
                f"This bid cannot be {value} as it is already {self.instance.status}."
            )
        
        if value not in ['accepted', 'rejected']:
            raise serializers.ValidationError(
                "Status must be either 'accepted' or 'rejected'."
            )
            
        return value

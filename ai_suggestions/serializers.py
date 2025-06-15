from rest_framework import serializers
from .models import AISuggestion, AIFeedbackLog
from users.serializers import PublicUserProfileSerializer
from services.serializers import ServiceDetailSerializer as ServiceSerializer
from django.utils import timezone
from decimal import Decimal

class AISuggestionListSerializer(serializers.ModelSerializer):
    """Serializer for listing AI suggestions"""
    suggestion_type_display = serializers.CharField(source='get_suggestion_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True, allow_null=True)
    
    class Meta:
        model = AISuggestion
        fields = [
            'id', 'suggestion_type', 'suggestion_type_display', 
            'title', 'service', 'service_title', 'status', 'status_display',
            'is_used', 'confidence_score', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

class AISuggestionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed AI suggestion view"""
    suggestion_type_display = serializers.CharField(source='get_suggestion_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user = PublicUserProfileSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    
    class Meta:
        model = AISuggestion
        fields = [
            'id', 'user', 'service', 'bid', 'suggestion_type', 
            'suggestion_type_display', 'title', 'content', 
            'suggested_amount', 'confidence_score', 'is_used',
            'status', 'status_display', 'viewed_at', 'used_at',
            'feedback', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

class AISuggestionFeedbackSerializer(serializers.Serializer):
    """Serializer for providing feedback on an AI suggestion"""
    feedback = serializers.CharField()
    is_used = serializers.BooleanField(required=False, default=False)
    status = serializers.ChoiceField(
        choices=['implemented', 'rejected', 'dismissed'],
        required=False,
        default='implemented'
    )
    
    def validate(self, data):
        # Check if the user is authorized to provide feedback
        user = self.context['request'].user
        suggestion = self.context.get('suggestion')
        
        if suggestion and suggestion.user != user:
            raise serializers.ValidationError(
                "You can only provide feedback on your own suggestions."
            )
            
        return data

class AIFeedbackLogSerializer(serializers.ModelSerializer):
    """Serializer for logging AI feedback"""
    
    class Meta:
        model = AIFeedbackLog
        fields = [
            'suggestion', 'interaction_type', 'interaction_data', 'bid'
        ]
    
    def validate(self, data):
        # Ensure at least one reference is provided
        if not data.get('suggestion') and not data.get('bid'):
            raise serializers.ValidationError(
                "Either suggestion or bid must be provided."
            )
            
        return data
    
    def create(self, validated_data):
        # Set the user from the request context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class BidAmountSuggestionSerializer(serializers.Serializer):
    """Serializer for requesting a bid amount suggestion"""
    service_id = serializers.UUIDField()
    customer_id = serializers.UUIDField()
    description = serializers.CharField(required=False)
    requirements = serializers.CharField(required=False)
    timeframe_days = serializers.IntegerField(required=False)

class BidMessageSuggestionSerializer(serializers.Serializer):
    """Serializer for requesting a bid message template suggestion"""
    service_id = serializers.UUIDField()
    customer_id = serializers.UUIDField()
    bid_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    timeframe_days = serializers.IntegerField(required=False)
    provider_expertise = serializers.CharField(required=False)
    message_tone = serializers.ChoiceField(
        choices=['professional', 'friendly', 'formal', 'casual'],
        required=False,
        default='professional'
    )

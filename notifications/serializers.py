from rest_framework import serializers
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationListSerializer(serializers.ModelSerializer):
    """Serializer for listing user notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'is_read',
            'action_url', 'created_at'
        ]
        read_only_fields = fields

class NotificationDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed notification view"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'is_read',
            'content_type', 'object_id', 'action_url', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    mark_all = serializers.BooleanField(default=False)
    
    def validate(self, data):
        # Either notification_ids or mark_all must be provided
        if not data.get('notification_ids') and not data.get('mark_all'):
            raise serializers.ValidationError(
                "Either provide notification_ids to mark specific notifications as read, "
                "or set mark_all=true to mark all notifications as read."
            )
        
        # If notification_ids is provided, validate them
        if data.get('notification_ids'):
            notifications = Notification.objects.filter(
                id__in=data.get('notification_ids'),
                recipient=self.context['request'].user
            )
            if len(notifications) != len(data.get('notification_ids')):
                raise serializers.ValidationError(
                    "One or more notification IDs are invalid or do not belong to you."
                )
        
        return data

class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating notifications
    This is primarily for internal use by the system, not exposed via API
    """
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'notification_type', 'title', 'message',
            'content_type', 'object_id', 'action_url'
        ]
        read_only_fields = ['id']

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Notification
from .serializers import NotificationSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        notification = serializer.save(user=self.request.user)
        self._broadcast_notification(notification)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().filter(is_read=False).update(is_read=True)
        
        # Get updated unread count
        unread_count = self.get_queryset().filter(is_read=False).count()
        
        # Broadcast updated count via WebSocket
        async_to_sync(channel_layer.group_send)(
            f'notifications_{request.user.id}',
            {
                'type': 'unread_count',
                'count': unread_count
            }
        )
        
        return Response({'status': 'notifications marked as read'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read"""
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save()

            # Get updated unread count
            unread_count = self.get_queryset().filter(is_read=False).count()
            
            # Broadcast updated count via WebSocket
            async_to_sync(channel_layer.group_send)(
                f'notifications_{request.user.id}',
                {
                    'type': 'unread_count',
                    'count': unread_count
                }
            )

        return Response({'status': 'notification marked as read'})

    def _broadcast_notification(self, notification):
        """Broadcast a new notification via WebSocket"""
        async_to_sync(channel_layer.group_send)(
            f'notifications_{notification.user.id}',
            {
                'type': 'notification',
                'notification': NotificationSerializer(notification).data
            }
        ) 
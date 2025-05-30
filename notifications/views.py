from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Notification
from .serializers import (
    NotificationListSerializer,
    NotificationDetailSerializer,
    NotificationMarkReadSerializer,
    NotificationCreateSerializer
)
from .permissions import IsNotificationRecipient

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for notifications - allows listing, retrieving, and managing notifications.
    Users can only see their own notifications.
    """
    queryset = Notification.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'is_read']
    ordering_fields = ['created_at']
    ordering = ['-created_at']  # Most recent first by default
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is not authenticated, return nothing
        if not user.is_authenticated:
            return Notification.objects.none()
            
        # Staff can see all notifications (optional, you might want to remove this)
        if user.is_staff and self.request.query_params.get('all'):
            return Notification.objects.all()
            
        # Users see only their own notifications
        return Notification.objects.filter(recipient=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NotificationDetailSerializer
        elif self.action in ['mark_read', 'update', 'partial_update']:
            return NotificationMarkReadSerializer
        elif self.action == 'create' and self.request.user.is_staff:
            # Only staff can create notifications through the API
            return NotificationCreateSerializer
        return NotificationListSerializer
    
    def get_permissions(self):
        if self.action in ['retrieve', 'destroy']:
            # Only the recipient can view or delete their notifications
            return [permissions.IsAuthenticated(), IsNotificationRecipient()]
        # List is filtered by user in get_queryset
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """
        Mark notifications as read.
        Can mark specific notifications or all of the user's notifications.
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            if serializer.validated_data.get('mark_all'):
                # Mark all user's notifications as read
                notifications = Notification.objects.filter(recipient=user, is_read=False)
                notifications.update(is_read=True)
                
                return Response({
                    'status': 'success',
                    'marked_count': notifications.count(),
                    'message': "All notifications marked as read."
                }, status=status.HTTP_200_OK)
            else:
                # Mark specific notifications as read
                notification_ids = serializer.validated_data.get('notification_ids')
                notifications = Notification.objects.filter(
                    id__in=notification_ids,
                    recipient=user,
                    is_read=False
                )
                notifications.update(is_read=True)
                
                return Response({
                    'status': 'success',
                    'marked_count': notifications.count(),
                    'message': "Notifications marked as read."
                }, status=status.HTTP_200_OK)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """
        Override update method to mark notifications as read using PUT.
        This provides the standard /api/v1/notifications/{id}/ endpoint with PUT method.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        
        if serializer.is_valid():
            # Ensure only the recipient can mark their notifications as read
            if instance.recipient != request.user:
                return Response(
                    {"error": "You can only mark your own notifications as read"},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            # Mark as read
            instance.is_read = True
            instance.save(update_fields=['is_read'])
            
            return Response({
                'status': 'success',
                'message': "Notification marked as read.",
                'notification_id': instance.id
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def partial_update(self, request, *args, **kwargs):
        """
        Override partial_update method to mark notifications as read using PATCH.
        """
        return self.update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Get count of unread notifications for the current user.
        """
        user = request.user
        
        # Count unread notifications
        unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
        
        # Get counts by notification type
        type_counts = Notification.objects.filter(recipient=user, is_read=False)\
            .values('notification_type')\
            .annotate(count=filters.Count('id'))
        
        type_data = {item['notification_type']: item['count'] for item in type_counts}
        
        return Response({
            'total_unread': unread_count,
            'type_counts': type_data
        }, status=status.HTTP_200_OK)

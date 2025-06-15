from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.contenttypes.models import ContentType
from .models import Notification
from django.utils import timezone

def send_notification(recipient, notification_type, title, message, content_object=None, action_url=None):
    """
    Create a notification in the database and send it via the channel layer.
    
    Args:
        recipient: User instance to receive the notification
        notification_type: Type of notification (from Notification.NOTIFICATION_TYPE_CHOICES)
        title: Notification title
        message: Notification message
        content_object: Related object (optional)
        action_url: URL to redirect to when the notification is clicked (optional)
    
    Returns:
        Notification instance
    """
    # Create notification in database
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        action_url=action_url,
    )
    
    # Link to content object if provided
    if content_object:
        content_type = ContentType.objects.get_for_model(content_object)
        notification.content_type = content_type
        notification.object_id = str(content_object.id)
        notification.save(update_fields=['content_type', 'object_id'])
    
    # Get channel layer and send to notification group
    channel_layer = get_channel_layer()
    
    # Construct notification data
    notification_data = {
        'type': 'notification_message',  # This matches the method name in NotificationConsumer
        'id': str(notification.id),
        'notification_type': notification_type,
        'title': title,
        'message': message,
        'timestamp': timezone.now().isoformat(),
    }
    
    # Add optional fields if present
    if content_object:
        notification_data['content_type'] = content_type.model
        notification_data['object_id'] = str(content_object.id)
    
    if action_url:
        notification_data['action_url'] = action_url
    
    # Send to the user's notification group
    async_to_sync(channel_layer.group_send)(
        f'notifications_{recipient.id}',
        notification_data
    )
    
    return notification

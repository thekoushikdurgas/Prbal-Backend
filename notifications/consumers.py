import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Notification, NotificationGroup
from uuid import UUID

# Placeholder for a push notification service
async def send_push_notification(user_id, title, message, data=None):
    # In a real application, this would integrate with a service like Firebase Cloud Messaging (FCM)
    # or Apple Push Notification service (APNs).
    # For now, we'll just print a message.
    print(f"Sending push notification to user {user_id}: {title} - {message} with data {data}")
    # Example: You would use a library like `firebase_admin` here to send the push notification.
    # from firebase_admin import messaging
    # message = messaging.Message(
    #     notification=messaging.Notification(title=title, body=message),
    #     token=user_device_token, # You'd retrieve this from a UserDevice model
    #     data=data
    # )
    # response = messaging.send(message)
    # print('Successfully sent message:', response)

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return
            
        self.user_id = str(user.id)
        self.notification_group_name = f'notifications_{self.user_id}'
        
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial unread count and recent notifications
        await self.send_unread_count()
        await self.send_recent_notifications()
    
    async def disconnect(self, close_code):
        # Leave notification group
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'mark_read':
            notification_id = data.get('notification_id')
            if notification_id:
                await self.mark_notification_read(notification_id)
                await self.send_unread_count() # Update count after marking read
                
                # Acknowledge the read status
                await self.send(text_data=json.dumps({
                    'type': 'notification_read',
                    'notification_id': notification_id
                }))
                
        elif message_type == 'mark_all_read':
            await self.mark_all_notifications_read()
            await self.send_unread_count()
            await self.send(text_data=json.dumps({'type': 'all_notifications_read'}))
            
        elif message_type == 'get_notifications':
            await self.send_recent_notifications()
            
        elif message_type == 'archive_notification':
            notification_id = data.get('notification_id')
            if notification_id:
                await self.archive_notification(notification_id)
                await self.send_recent_notifications()
                await self.send_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'notification_archived',
                    'notification_id': notification_id
                }))

    # Receive notification from notification group (called by send_notification utility)
    async def send_notification_to_consumer(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'id': event['id'],
            'notification_type': event['notification_type'],
            'title': event['title'],
            'message': event['message'],
            'content_type': event.get('content_type'),
            'object_id': event.get('object_id'),
            'action_url': event.get('action_url'),
            'timestamp': event['timestamp'],
            'is_read': event['is_read'],
            'group_id': event.get('group_id')
        }))
        
        # Optionally send push notification
        if event.get('send_push', False):
            await send_push_notification(
                user_id=self.user_id,
                title=event['title'],
                message=event['message'],
                data={'notification_id': event['id'], 'type': event['notification_type']}
            )
            
    async def notification_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification_count',
            'unread_count': event['unread_count']
        }))
        
    async def notification_list_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification_list',
            'notifications': event['notifications']
        }))

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = Notification.objects.get(
                id=UUID(notification_id),
                recipient=self.scope['user']
            )
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return True
        except (Notification.DoesNotExist, ValueError):
            return False
            
    @database_sync_to_async
    def mark_all_notifications_read(self):
        Notification.objects.filter(
            recipient=self.scope['user'],
            is_read=False
        ).update(is_read=True)
        
    @database_sync_to_async
    def archive_notification(self, notification_id):
        try:
            notification = Notification.objects.get(
                id=UUID(notification_id),
                recipient=self.scope['user']
            )
            notification.is_archived = True
            notification.save(update_fields=['is_archived'])
            return True
        except (Notification.DoesNotExist, ValueError):
            return False
            
    @database_sync_to_async
    def get_unread_notification_count(self):
        return Notification.objects.filter(
            recipient=self.scope['user'],
            is_read=False,
            is_archived=False
        ).count()
        
    @database_sync_to_async
    def get_recent_notifications(self, limit=10):
        notifications = Notification.objects.filter(
            recipient=self.scope['user'],
            is_archived=False
        ).order_by('-created_at')[:limit]
        
        # Serialize notifications for sending over WebSocket
        serialized_notifications = []
        for notification in notifications:
            serialized_notifications.append({
                'id': str(notification.id),
                'notification_type': notification.notification_type,
                'title': notification.title,
                'message': notification.message,
                'is_read': notification.is_read,
                'action_url': notification.action_url,
                'timestamp': notification.created_at.isoformat(),
                'group_id': str(notification.group.id) if notification.group else None
            })
        return serialized_notifications
        
    async def send_unread_count(self):
        unread_count = await self.get_unread_notification_count()
        await self.channel_layer.group_send(
            self.notification_group_name,
            {
                'type': 'notification_count_update',
                'unread_count': unread_count
            }
        )
        
    async def send_recent_notifications(self):
        recent_notifications = await self.get_recent_notifications()
        await self.channel_layer.group_send(
            self.notification_group_name,
            {
                'type': 'notification_list_update',
                'notifications': recent_notifications
            }
        )

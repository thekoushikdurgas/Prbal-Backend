import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import MessageThread, Message, UserPresence
from uuid import UUID
from asgiref.sync import sync_to_async
from django.core.cache import cache

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'chat_{self.thread_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Check if user is a participant in this thread
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return
            
        thread_exists = await self.check_thread_permission(user)
        if not thread_exists:
            await self.close()
            return
        
        # Mark user as online in this thread
        await self.update_user_presence(user, True)
        
        # Notify other participants about user's online status
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence_update',
                'user_id': str(user.id),
                'status': 'online',
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Update user's presence status when disconnecting
        user = self.scope['user']
        if user.is_authenticated:
            await self.update_user_presence(user, False)
            
            # Notify other participants about user's offline status
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'presence_update',
                    'user_id': str(user.id),
                    'status': 'offline',
                    'timestamp': timezone.now().isoformat(),
                }
            )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        user = self.scope['user']
        
        # Handle different types of WebSocket messages
        if message_type == 'message':
            message_content = data.get('message', '')
            
            if not message_content.strip():
                return
                
            # Save message to database
            message = await self.save_message(user, message_content)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'sender_id': str(user.id),
                    'sender_name': user.get_full_name() or user.username,
                    'message_id': str(message.id),
                    'timestamp': message.created_at.isoformat(),
                    'status': 'sent'
                }
            )
            
        elif message_type == 'typing':
            # Handle typing indicator
            is_typing = data.get('is_typing', False)
            
            # Cache typing status with 5-second expiration
            cache_key = f"typing_{self.thread_id}_{user.id}"
            await sync_to_async(cache.set)(cache_key, is_typing, 5)
            
            # Broadcast typing status to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(user.id),
                    'is_typing': is_typing
                }
            )
            
        elif message_type == 'read_receipt':
            # Handle read receipts
            message_id = data.get('message_id')
            if message_id:
                await self.mark_as_read(message_id, user)
                
                # Broadcast read receipt to the group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_read',
                        'user_id': str(user.id),
                        'message_id': message_id,
                        'timestamp': timezone.now().isoformat()
                    }
                )
    
    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
            'status': event.get('status', 'sent')
        }))
        
    # Handle typing indicator broadcasts
    async def typing_indicator(self, event):
        # Send typing status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        }))
    
    # Handle message read receipts
    async def message_read(self, event):
        # Send read receipt to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'user_id': event['user_id'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp']
        }))
        
    # Handle presence updates
    async def presence_update(self, event):
        # Send presence update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'user_id': event['user_id'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def check_thread_permission(self, user):
        try:
            thread = MessageThread.objects.get(id=UUID(self.thread_id))
            return thread.participants.filter(id=user.id).exists()
        except (MessageThread.DoesNotExist, ValueError):
            return False
    
    @database_sync_to_async
    def save_message(self, user, message_content):
        thread = MessageThread.objects.get(id=UUID(self.thread_id))
        message = Message.objects.create(
            thread=thread,
            sender=user,
            content=message_content,
            status='sent'
        )
        # Update the thread's updated_at timestamp
        thread.updated_at = timezone.now()
        thread.save(update_fields=['updated_at'])
        
        return message
        
    @database_sync_to_async
    def mark_as_read(self, message_id, user):
        try:
            message = Message.objects.get(id=UUID(message_id))
            if message.thread_id == UUID(self.thread_id) and message.sender_id != user.id:
                message.read_by.add(user)
                message.status = 'read'
                message.save(update_fields=['status'])
                return True
        except (Message.DoesNotExist, ValueError):
            pass
        return False
        
    @database_sync_to_async
    def update_user_presence(self, user, is_online):
        # Update or create presence record
        presence, _ = UserPresence.objects.update_or_create(
            user=user,
            defaults={'is_online': is_online, 'last_seen': timezone.now()}
        )
        return presence

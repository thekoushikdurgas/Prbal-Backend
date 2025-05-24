import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Chat, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']

        # Check if user has access to this chat
        if not await self.can_access_chat():
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Mark any unread messages as read
        await self.mark_messages_read()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'message')
        
        if message_type == 'message':
            content = text_data_json['content']
            
            # Save message to database
            message = await self.save_message(content)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'content': content,
                        'sender_id': self.user.id,
                        'sender_name': self.user.get_full_name(),
                        'timestamp': message.created_at.isoformat(),
                    }
                }
            )
        elif message_type == 'typing':
            # Broadcast typing status
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'user_id': self.user.id,
                    'is_typing': text_data_json.get('is_typing', False)
                }
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))

    async def typing_status(self, event):
        # Send typing status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        }))

    @database_sync_to_async
    def can_access_chat(self):
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return chat.can_participate(self.user)
        except Chat.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        chat = Chat.objects.get(id=self.chat_id)
        message = Message.objects.create(
            chat=chat,
            sender=self.user,
            content=content
        )
        # Update chat's updated_at timestamp
        chat.save()  # This triggers auto_now=True on updated_at
        return message

    @database_sync_to_async
    def mark_messages_read(self):
        chat = Chat.objects.get(id=self.chat_id)
        unread_messages = Message.objects.filter(
            chat=chat
        ).exclude(
            sender=self.user
        ).exclude(
            read_by=self.user
        )
        
        for message in unread_messages:
            message.read_by.add(self.user) 
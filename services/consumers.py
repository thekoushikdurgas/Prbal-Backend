import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Booking, ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.booking_id = self.scope['url_route']['kwargs']['booking_id']
        self.room_group_name = f'chat_{self.booking_id}'
        self.user = self.scope['user']

        # Check if user has access to this booking's chat
        if not await self.can_access_chat():
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

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
            message = text_data_json['message']
            
            # Save message to database
            chat_message = await self.save_message(message)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name(),
                    'timestamp': chat_message.timestamp.isoformat(),
                    'message_id': chat_message.id
                }
            )
        elif message_type == 'read_receipt':
            message_id = text_data_json['message_id']
            
            # Mark message as read
            await self.mark_message_read(message_id)
            
            # Send read receipt to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'message_id': message_id,
                    'reader_id': self.user.id,
                    'read_at': timezone.now().isoformat()
                }
            )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    async def read_receipt(self, event):
        # Send read receipt to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'reader_id': event['reader_id'],
            'read_at': event['read_at']
        }))

    @database_sync_to_async
    def can_access_chat(self):
        try:
            booking = Booking.objects.get(id=self.booking_id)
            return self.user in [booking.customer, booking.provider]
        except Booking.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, message_text):
        booking = Booking.objects.get(id=self.booking_id)
        return ChatMessage.objects.create(
            booking=booking,
            sender=self.user,
            text_content=message_text
        )

    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            message = ChatMessage.objects.get(id=message_id, booking_id=self.booking_id)
            # Only mark as read if the user is the recipient
            if self.user != message.sender and not message.read_at:
                message.read_at = timezone.now()
                message.save()
        except ChatMessage.DoesNotExist:
            pass 
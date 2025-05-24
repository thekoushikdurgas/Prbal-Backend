from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Chat, Message, Booking, ServiceRequest
from .chat_serializers import ChatListSerializer, ChatDetailSerializer, MessageSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Chat.objects.filter(participants=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatListSerializer
        return ChatDetailSerializer

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in the chat"""
        chat = self.get_object()
        if not chat.can_participate(request.user):
            return Response(
                {"detail": "You cannot participate in this chat."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.save(
                chat=chat,
                sender=request.user
            )

            # Broadcast via WebSocket
            async_to_sync(channel_layer.group_send)(
                f'chat_{chat.id}',
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sender_id': request.user.id,
                        'sender_name': request.user.get_full_name(),
                        'timestamp': message.created_at.isoformat(),
                    }
                }
            )

            return Response(
                MessageSerializer(message, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark all messages in the chat as read"""
        chat = self.get_object()
        if not chat.can_participate(request.user):
            return Response(
                {"detail": "You cannot access this chat."},
                status=status.HTTP_403_FORBIDDEN
            )

        Message.objects.filter(
            chat=chat
        ).exclude(
            sender=request.user
        ).exclude(
            read_by=request.user
        ).update(
            read_by=request.user
        )

        return Response({'status': 'messages marked as read'})

    @action(detail=False, methods=['post'])
    def create_or_get(self, request):
        """Create a new chat or get existing one"""
        booking_id = request.data.get('booking_id')
        service_request_id = request.data.get('service_request_id')
        other_user_id = request.data.get('user_id')

        if booking_id:
            booking = get_object_or_404(Booking, id=booking_id)
            if request.user not in [booking.customer, booking.provider]:
                return Response(
                    {"detail": "You are not part of this booking."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            chat, created = Chat.objects.get_or_create(booking=booking)
            if created:
                chat.participants.add(booking.customer, booking.provider)

        elif service_request_id:
            service_request = get_object_or_404(ServiceRequest, id=service_request_id)
            if request.user not in [service_request.customer, service_request.provider]:
                return Response(
                    {"detail": "You are not part of this service request."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            chat, created = Chat.objects.get_or_create(service_request=service_request)
            if created:
                chat.participants.add(service_request.customer, service_request.provider)

        elif other_user_id:
            # Direct chat between two users
            chat = Chat.objects.filter(
                participants=request.user
            ).filter(
                participants=other_user_id
            ).filter(
                booking__isnull=True,
                service_request__isnull=True
            ).first()

            if not chat:
                chat = Chat.objects.create()
                chat.participants.add(request.user, other_user_id)

        else:
            return Response(
                {"detail": "Must provide booking_id, service_request_id, or user_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            ChatDetailSerializer(chat, context={'request': request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        ) 
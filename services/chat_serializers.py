from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat, Message

User = get_user_model()

class ChatParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'user_type', 'profile_image']

class MessageSerializer(serializers.ModelSerializer):
    sender = ChatParticipantSerializer(read_only=True)
    is_read = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'sender', 'content', 'media_file',
            'created_at', 'is_read', 'read_by'
        ]
        read_only_fields = ['chat', 'sender', 'created_at', 'read_by']

    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and request.user != obj.sender:
            return obj.read_by.filter(id=request.user.id).exists()
        return True

class ChatListSerializer(serializers.ModelSerializer):
    participants = ChatParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = [
            'id', 'participants', 'booking', 'service_request',
            'created_at', 'updated_at', 'last_message', 'unread_count'
        ]

    def get_last_message(self, obj):
        last_message = obj.messages.first()  # Due to ordering = ['created_at']
        if last_message:
            return MessageSerializer(last_message, context=self.context).data
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request:
            return obj.messages.exclude(sender=request.user).exclude(read_by=request.user).count()
        return 0

class ChatDetailSerializer(ChatListSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta(ChatListSerializer.Meta):
        fields = ChatListSerializer.Meta.fields + ['messages'] 
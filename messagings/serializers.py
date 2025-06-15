from rest_framework import serializers
from .models import MessageThread, Message
from users.serializers import PublicUserProfileSerializer
from django.contrib.auth import get_user_model
import base64
from django.core.files.base import ContentFile
import uuid

User = get_user_model()

class MessageListSerializer(serializers.ModelSerializer):
    """Serializer for listing messages in a thread"""
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_profile_picture = serializers.ImageField(source='sender.profile_picture', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_name', 'sender_profile_picture', 
            'content', 'attachment', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'created_at']

class Base64FileField(serializers.FileField):
    """Custom field for handling base64 encoded files"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:'):
            # Base64 encoded file - decode
            format, filestr = data.split(';base64,') 
            ext = format.split('/')[-1] 
            
            data = ContentFile(
                base64.b64decode(filestr),
                name=f"{uuid.uuid4()}.{ext}"
            )
            
        return super().to_internal_value(data)

class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new message"""
    attachment = Base64FileField(required=False)
    
    class Meta:
        model = Message
        fields = ['id', 'thread', 'content', 'attachment']
        read_only_fields = ['id']
    
    def validate_thread(self, value):
        # Check if user is a participant in the thread
        if self.context['request'].user not in value.participants.all():
            raise serializers.ValidationError(
                "You must be a participant in this thread to send a message."
            )
        return value
    
    def create(self, validated_data):
        # Set the sender to the current user
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)

class ThreadParticipantSerializer(serializers.ModelSerializer):
    """Serializer for thread participants"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'profile_picture', 'user_type'
        ]
        read_only_fields = fields

class MessageThreadListSerializer(serializers.ModelSerializer):
    """Serializer for listing message threads"""
    participants = ThreadParticipantSerializer(many=True, read_only=True)
    last_message_preview = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageThread
        fields = [
            'id', 'participants', 'thread_type', 'bid', 'booking',
            'last_message_preview', 'unread_count', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_last_message_preview(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'sender_name': last_message.sender.get_full_name(),
                'content': last_message.content[:50] + ('...' if len(last_message.content) > 50 else ''),
                'created_at': last_message.created_at
            }
        return None
    
    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.exclude(sender=user).exclude(read_by=user).count()

class MessageThreadCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new message thread"""
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True
    )
    initial_message = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = MessageThread
        fields = [
            'id', 'thread_type', 'bid', 'booking', 
            'participant_ids', 'initial_message'
        ]
        read_only_fields = ['id']
    
    def validate_participant_ids(self, value):
        # Check that all participant IDs are valid
        users = User.objects.filter(id__in=value)
        if len(users) != len(value):
            raise serializers.ValidationError(
                "One or more participant IDs are invalid."
            )
        
        # Ensure the current user is included in the participants
        if self.context['request'].user.id not in value:
            value.append(str(self.context['request'].user.id))
            
        return value
    
    def validate(self, data):
        # Validate based on thread_type
        thread_type = data.get('thread_type')
        
        if thread_type == 'bid':
            if not data.get('bid'):
                raise serializers.ValidationError(
                    {"bid": "Bid ID is required for bid-related threads."}
                )
            # Ensure bid participants match thread participants
            bid = data.get('bid')
            required_participants = [bid.provider.id, bid.service.provider.id]
            for participant_id in required_participants:
                if str(participant_id) not in data.get('participant_ids'):
                    raise serializers.ValidationError(
                        {"participant_ids": "Bid-related threads must include the bid provider and service provider."}
                    )
                    
        elif thread_type == 'booking':
            if not data.get('booking'):
                raise serializers.ValidationError(
                    {"booking": "Booking ID is required for booking-related threads."}
                )
            # Ensure booking participants match thread participants
            booking = data.get('booking')
            required_participants = [booking.customer.id, booking.provider.id]
            for participant_id in required_participants:
                if str(participant_id) not in data.get('participant_ids'):
                    raise serializers.ValidationError(
                        {"participant_ids": "Booking-related threads must include the booking customer and provider."}
                    )
        
        return data
    
    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids')
        initial_message = validated_data.pop('initial_message', None)
        
        # Create the thread
        thread = MessageThread.objects.create(**validated_data)
        
        # Add participants
        for participant_id in participant_ids:
            user = User.objects.get(id=participant_id)
            thread.participants.add(user)
        
        # Create initial message if provided
        if initial_message:
            Message.objects.create(
                thread=thread,
                sender=self.context['request'].user,
                content=initial_message
            )
        
        return thread

class MessageThreadDetailSerializer(serializers.ModelSerializer):
    """Serializer for thread details with participants"""
    participants = ThreadParticipantSerializer(many=True, read_only=True)
    
    class Meta:
        model = MessageThread
        fields = [
            'id', 'participants', 'thread_type', 'bid', 'booking',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

class MessageReadStatusUpdateSerializer(serializers.Serializer):
    """Serializer for marking messages as read"""
    message_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    mark_all_in_thread = serializers.BooleanField(default=False)
    thread_id = serializers.UUIDField(required=False)
    
    def validate(self, data):
        # Either message_ids or (mark_all_in_thread and thread_id) must be provided
        if not data.get('message_ids') and not (data.get('mark_all_in_thread') and data.get('thread_id')):
            raise serializers.ValidationError(
                "Either provide message_ids to mark specific messages as read, "
                "or set mark_all_in_thread=true and provide thread_id to mark all messages in a thread as read."
            )
        
        # If thread_id is provided, validate it
        if data.get('thread_id'):
            try:
                thread = MessageThread.objects.get(id=data.get('thread_id'))
                if self.context['request'].user not in thread.participants.all():
                    raise serializers.ValidationError(
                        {"thread_id": "You must be a participant in this thread."}
                    )
            except MessageThread.DoesNotExist:
                raise serializers.ValidationError(
                    {"thread_id": "Thread not found."}
                )
        
        # If message_ids is provided, validate them
        if data.get('message_ids'):
            messages = Message.objects.filter(id__in=data.get('message_ids'))
            if len(messages) != len(data.get('message_ids')):
                raise serializers.ValidationError(
                    {"message_ids": "One or more message IDs are invalid."}
                )
            
            # Check if user is a participant in all message threads
            for message in messages:
                if self.context['request'].user not in message.thread.participants.all():
                    raise serializers.ValidationError(
                        {"message_ids": "You must be a participant in all message threads."}
                    )
        
        return data

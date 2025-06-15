from rest_framework import viewsets, permissions, status, filters, generics, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F, Count, Max
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import MessageThread, Message
from .serializers import (
    MessageThreadListSerializer,
    MessageThreadDetailSerializer,
    MessageThreadCreateSerializer,
    MessageListSerializer,
    MessageCreateSerializer,
    MessageReadStatusUpdateSerializer
)
from .permissions import IsThreadParticipant, IsMessageSender

class MessageThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for message threads - allows listing, creating, and retrieving threads.
    Users can only see threads they are participants in.
    """
    queryset = MessageThread.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['thread_type']
    ordering_fields = ['updated_at', 'created_at']
    ordering = ['-updated_at']  # Most recently updated first by default
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is not authenticated, return nothing
        if not user.is_authenticated:
            return MessageThread.objects.none()
            
        # Users see only threads they're part of
        return MessageThread.objects.filter(participants=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MessageThreadDetailSerializer
        elif self.action == 'create':
            return MessageThreadCreateSerializer
        return MessageThreadListSerializer
    
    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # Only participants can view, update, or delete a thread
            return [permissions.IsAuthenticated(), IsThreadParticipant()]
        # List and create are handled by get_queryset and serializer validation
        return [permissions.IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get all messages in a thread.
        Can be filtered by 'since' parameter (timestamp) to get only newer messages.
        """
        thread = self.get_object()
        
        # Check for 'since' parameter (timestamp to get messages after)
        since_param = request.query_params.get('since')
        if since_param:
            try:
                since_date = timezone.datetime.fromtimestamp(float(since_param), tz=timezone.get_current_timezone())
                messages = thread.messages.filter(created_at__gt=since_date).order_by('created_at')
            except (ValueError, OverflowError):
                return Response({
                    'error': 'Invalid timestamp format for "since" parameter'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Get all messages in the thread, ordered by creation time
            messages = thread.messages.all().order_by('created_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageListSerializer(messages, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for messages - allows creating, retrieving, and updating messages.
    Users can only see messages in threads they are participants in.
    """
    queryset = Message.objects.all()
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is not authenticated, return nothing
        if not user.is_authenticated:
            return Message.objects.none()
            
        # Users see only messages in threads they're part of
        return Message.objects.filter(thread__participants=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageListSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only the sender can update or delete their messages
            return [permissions.IsAuthenticated(), IsMessageSender()]
        elif self.action in ['retrieve']:
            # Only thread participants can view messages
            return [permissions.IsAuthenticated(), IsThreadParticipant()]
        # Create is validated in the serializer
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        """
        Mark messages as read by the current user.
        Can mark specific messages or all messages in a thread.
        """
        serializer = MessageReadStatusUpdateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            
            if serializer.validated_data.get('mark_all_in_thread'):
                # Mark all messages in a thread as read
                thread_id = serializer.validated_data.get('thread_id')
                thread = MessageThread.objects.get(id=thread_id)
                
                # Only mark messages not sent by the user
                messages_to_mark = thread.messages.exclude(sender=user)
                
                # Add user to read_by for all these messages
                for message in messages_to_mark:
                    message.read_by.add(user)
                
                return Response({
                    'status': 'success',
                    'marked_count': messages_to_mark.count(),
                    'message': "All messages in thread marked as read."
                }, status=status.HTTP_200_OK)
            else:
                # Mark specific messages as read
                message_ids = serializer.validated_data.get('message_ids')
                messages = Message.objects.filter(id__in=message_ids)
                
                # Add user to read_by for all these messages
                for message in messages:
                    message.read_by.add(user)
                
                return Response({
                    'status': 'success',
                    'marked_count': len(message_ids),
                    'message': "Messages marked as read."
                }, status=status.HTTP_200_OK)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Get count of unread messages for the current user.
        Can be filtered by thread if thread_id is provided.
        """
        user = request.user
        thread_id = request.query_params.get('thread_id')
        
        # Base query: messages not sent by the user and not marked as read by the user
        query = Message.objects.exclude(sender=user).exclude(read_by=user)
        
        # Filter by thread if specified
        if thread_id:
            query = query.filter(thread_id=thread_id)
        else:
            # Only include threads the user is a participant in
            query = query.filter(thread__participants=user)
        
        # Get the count
        unread_count = query.count()
        
        # Get unread count by thread
        if not thread_id:
            thread_counts = query.values('thread').annotate(count=Count('id'))
            thread_data = {str(item['thread']): item['count'] for item in thread_counts}
        else:
            thread_data = {thread_id: unread_count}
        
        return Response({
            'total_unread': unread_count,
            'thread_counts': thread_data
        }, status=status.HTTP_200_OK)


class ThreadMessagesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    """
    ViewSet for messages within a specific thread - allows listing and creating messages.
    Implements the /api/messages/{thread}/ (GET, POST) endpoint.
    """
    permission_classes = [permissions.IsAuthenticated, IsThreadParticipant]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageListSerializer
    
    def get_queryset(self):
        thread_id = self.kwargs.get('thread_id')
        thread = get_object_or_404(MessageThread, id=thread_id)
        
        # Check if user is a participant in the thread
        if self.request.user not in thread.participants.all():
            return Message.objects.none()
        
        # Get all messages in the thread, ordered by creation time
        return thread.messages.all().order_by('created_at')
    
    def list(self, request, *args, **kwargs):
        """
        Get all messages in a thread.
        Can be filtered by 'since' parameter (timestamp) to get only newer messages.
        """
        thread_id = self.kwargs.get('thread_id')
        thread = get_object_or_404(MessageThread, id=thread_id)
        
        # Check for 'since' parameter (timestamp to get messages after)
        since_param = request.query_params.get('since')
        if since_param:
            try:
                since_date = timezone.datetime.fromtimestamp(float(since_param), tz=timezone.get_current_timezone())
                messages = thread.messages.filter(created_at__gt=since_date).order_by('created_at')
            except (ValueError, OverflowError):
                return Response({
                    'error': 'Invalid timestamp format for "since" parameter'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Get all messages in the thread, ordered by creation time
            messages = thread.messages.all().order_by('created_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new message in the thread.
        """
        thread_id = self.kwargs.get('thread_id')
        thread = get_object_or_404(MessageThread, id=thread_id)
        
        # Check if user is a participant in the thread
        if request.user not in thread.participants.all():
            return Response({
                'error': 'You must be a participant in this thread to send a message.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Add the thread ID to the request data
        mutable_data = request.data.copy()
        mutable_data['thread'] = thread.id
        
        serializer = self.get_serializer(data=mutable_data)
        serializer.is_valid(raise_exception=True)
        
        # Set the sender to the current user and save
        serializer.validated_data['sender'] = request.user
        self.perform_create(serializer)
        
        # Update the thread's updated_at timestamp
        thread.save(update_fields=['updated_at'])
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone
from bids.models import Bid
from bookings.models import Booking

class MessageThread(models.Model):
    """
    Represents a conversation thread between two or more users,
    typically associated with a bid or booking.
    """
    THREAD_TYPE_CHOICES = (
        ('bid', 'Bid Related'),
        ('booking', 'Booking Related'),
        ('general', 'General Inquiry'),
        ('support', 'Customer Support'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='message_threads')
    thread_type = models.CharField(max_length=20, choices=THREAD_TYPE_CHOICES)
    bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, null=True, blank=True, related_name='message_threads')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='message_threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Message Thread'
        verbose_name_plural = 'Message Threads'
    
    def __str__(self):
        participant_names = ', '.join([str(p) for p in self.participants.all()[:3]])
        if self.participants.count() > 3:
            participant_names += f" and {self.participants.count() - 3} more"
        return f"Thread between {participant_names} - {self.thread_type}"

class Message(models.Model):
    """
    Represents a single message within a conversation thread.
    """
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_sent')
    content = models.TextField()
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True)
    is_read = models.BooleanField(default=False)  # Legacy field, kept for backward compatibility
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='messages_read', 
        blank=True,
        through='MessageReadReceipt'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
    
    def __str__(self):
        return f"Message from {self.sender} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class MessageReadReceipt(models.Model):
    """
    Tracks when each user read a specific message.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_receipts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')
        verbose_name = 'Message Read Receipt'
        verbose_name_plural = 'Message Read Receipts'
        
    def __str__(self):
        return f"{self.user} read message at {self.read_at.strftime('%Y-%m-%d %H:%M')}"


class UserPresence(models.Model):
    """
    Tracks the online/offline status of users.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='presence')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    last_activity = models.CharField(max_length=255, blank=True, null=True)
    device_info = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'User Presence'
        verbose_name_plural = 'User Presences'
        
    def __str__(self):
        status = "Online" if self.is_online else f"Last seen {self.last_seen.strftime('%Y-%m-%d %H:%M')}"
        return f"{self.user} - {status}"

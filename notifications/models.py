from django.db import models
from django.conf import settings
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class NotificationGroup(models.Model):
    """
    Represents a logical grouping for notifications.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Notification Group'
        verbose_name_plural = 'Notification Groups'

    def __str__(self):
        return self.name


class Notification(models.Model):
    """
    Represents a notification sent to a user about various events in the system.
    Uses Generic Foreign Keys to link to any model instance (e.g., booking, bid, payment).
    """
    NOTIFICATION_TYPE_CHOICES = (
        ('bid_received', 'Bid Received'),
        ('bid_accepted', 'Bid Accepted'),
        ('bid_rejected', 'Bid Rejected'),
        ('booking_created', 'Booking Created'),
        ('booking_status_updated', 'Booking Status Updated'),
        ('payment_received', 'Payment Received'),
        ('payout_processed', 'Payout Processed'),
        ('message_received', 'Message Received'),
        ('review_received', 'Review Received'),
        ('verification_updated', 'Verification Status Updated'),
        ('system', 'System Notification'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    group = models.ForeignKey(NotificationGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    
    # Generic Foreign Key to the related object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # URL for redirecting when notification is clicked
    action_url = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.notification_type} for {self.recipient} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

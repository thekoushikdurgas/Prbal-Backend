from django.db import models
from django.conf import settings
import uuid
from services.models import Service

# Create your models here.
class Bid(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    CURRENCY_CHOICES = (
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    )
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids_requested')
    service_provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids_offered')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bids')
    
    # Pricing and scheduling
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    duration = models.CharField(max_length=50, help_text='Proposed duration for the service')
    scheduled_date_time = models.DateTimeField(help_text='Proposed date and time for the service')
    
    # Status and lifecycle timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Communication and details
    message = models.TextField(help_text='Message from the provider with the bid')
    location = models.CharField(max_length=255, help_text='Location relevant to the bid')
    payment_details = models.JSONField(default=dict, blank=True, null=True)
    
    # AI suggestion related fields
    is_ai_suggested = models.BooleanField(default=False, help_text='Whether this bid was created based on an AI suggestion')
    ai_suggested_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='The AI suggested amount')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bid'
        verbose_name_plural = 'Bids'
    
    def __str__(self):
        return f"{self.service_provider.username}'s bid on {self.service.name}"
    
    # For backward compatibility
    @property
    def provider(self):
        return self.service_provider
    
    @property
    def description(self):
        return self.message
        
    @property
    def estimated_delivery_time(self):
        """For backward compatibility"""
        # Try to extract numeric value from duration string if possible
        import re
        match = re.search(r'\d+', self.duration)
        if match:
            return int(match.group())
        return 0
    
    # Status update methods
    def accept(self):
        """Mark the bid as accepted and set timestamp"""
        from django.utils import timezone
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
    
    def reject(self):
        """Mark the bid as rejected and set timestamp"""
        from django.utils import timezone
        self.status = 'rejected'
        self.rejected_at = timezone.now()
        self.save()
    
    def complete(self):
        """Mark the bid as completed and set timestamp"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def cancel(self):
        """Mark the bid as cancelled and set timestamp"""
        from django.utils import timezone
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()

from django.db import models
from django.conf import settings
import uuid
from services.models import Service, ServiceCategory
from django.utils import timezone
from bids.models import Bid
from decimal import Decimal

# Create your models here.
class AISuggestion(models.Model):
    SUGGESTION_TYPE_CHOICES = (
        ('service_improvement', 'Service Improvement'),
        ('pricing', 'Pricing Recommendation'),
        ('bid_amount', 'Bid Amount Suggestion'),
        ('bid_message', 'Bid Message Template'),
        ('category', 'Category Recommendation'),
        ('marketing', 'Marketing Tip'),
        ('general', 'General Suggestion'),
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('viewed', 'Viewed'),
        ('implemented', 'Implemented'),
        ('rejected', 'Rejected'),
        ('dismissed', 'Dismissed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_suggestions')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, related_name='ai_suggestions', null=True, blank=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, related_name='ai_suggestions', null=True, blank=True)
    bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, related_name='ai_suggestions', null=True, blank=True)
    suggestion_type = models.CharField(max_length=30, choices=SUGGESTION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    suggested_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confidence_score = models.FloatField(default=0.5, help_text="Confidence level of the AI for this suggestion (0-1)")
    is_used = models.BooleanField(default=False, help_text="Indicates if the suggestion was used by the user")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    viewed_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    feedback = models.TextField(blank=True, help_text="User feedback on this suggestion")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Suggestion'
        verbose_name_plural = 'AI Suggestions'
    
    def __str__(self):
        return f"{self.suggestion_type} suggestion for {self.user.username}"
    
    def mark_as_viewed(self):
        """Mark this suggestion as viewed by the user"""
        self.status = 'viewed'
        self.viewed_at = timezone.now()
        self.save()
    
    def mark_as_used(self):
        """Mark this suggestion as used by the user"""
        self.is_used = True
        self.status = 'implemented'
        self.used_at = timezone.now()
        self.save()
    
    def add_feedback(self, feedback_text, status='implemented'):
        """Add user feedback to this suggestion"""
        self.feedback = feedback_text
        self.status = status
        self.save()

class AIFeedbackLog(models.Model):
    """Model for tracking user interactions with AI suggestions for model improvement"""
    INTERACTION_TYPE_CHOICES = (
        ('view', 'Viewed Suggestion'),
        ('use', 'Used Suggestion'),
        ('accept_bid', 'Accepted Bid with Suggestion'),
        ('complete_booking', 'Completed Booking with Suggestion'),
        ('feedback', 'Provided Feedback'),
        ('reject', 'Rejected Suggestion'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_feedback_logs')
    suggestion = models.ForeignKey(AISuggestion, on_delete=models.CASCADE, related_name='feedback_logs', null=True, blank=True)
    interaction_type = models.CharField(max_length=30, choices=INTERACTION_TYPE_CHOICES)
    interaction_data = models.JSONField(blank=True, null=True, help_text="Additional data about the interaction")
    bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, related_name='ai_feedback_logs', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Feedback Log'
        verbose_name_plural = 'AI Feedback Logs'
    
    def __str__(self):
        return f"{self.interaction_type} by {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"


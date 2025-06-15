from django.db import models
from django.conf import settings
import uuid
from services.models import Service
from bids.models import Bid

# Create your models here.
class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    )
    
    CANCELLATION_REASON_CHOICES = (
        ('customer_request', 'Customer Request'),
        ('provider_unavailable', 'Provider Unavailable'),
        ('rescheduled', 'Rescheduled to New Date'),
        ('payment_issue', 'Payment Issue'),
        ('service_issue', 'Service Issue'),
        ('other', 'Other Reason'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_bookings')
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='provider_bookings')
    bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, related_name='bookings', null=True, blank=True)
    
    # Date and time fields
    booking_date = models.DateField(help_text="Date of the booking")
    start_time = models.TimeField(help_text="Start time of the booking")
    end_time = models.TimeField(help_text="End time of the booking")
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Location fields
    address = models.TextField(help_text="Address where the service will take place", blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude coordinate")
    
    # Payment fields
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total cost of the booking")
    payment_details = models.JSONField(null=True, blank=True, help_text="Details about the payment for this booking")
    
    # Status and requirement fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requirements = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Review fields
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, help_text="Rating given for this booking")
    review = models.TextField(null=True, blank=True, help_text="Text review for this booking")
    
    # Rescheduling fields
    is_rescheduled = models.BooleanField(default=False)
    original_booking_date = models.DateTimeField(null=True, blank=True)
    rescheduled_date = models.DateField(null=True, blank=True, help_text="New date if rescheduled")
    rescheduled_count = models.PositiveSmallIntegerField(default=0)
    rescheduled_reason = models.TextField(blank=True, null=True)
    
    # Cancellation fields
    cancellation_reason = models.CharField(max_length=50, choices=CANCELLATION_REASON_CHOICES, null=True, blank=True)
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='cancelled_bookings')
    cancellation_date = models.DateTimeField(null=True, blank=True)
    
    # Calendar sync info
    calendar_event_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID of synced calendar event")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
    
    def __str__(self):
        return f"Booking #{self.id} - {self.service.title}"
    
    def confirm(self):
        """Confirm a pending booking"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
    
    def start_service(self):
        """Mark booking as in progress"""
        if self.status == 'confirmed':
            self.status = 'in_progress'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
    
    def complete(self):
        """Mark booking as completed"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.completion_date = models.functions.Now()
            self.save(update_fields=['status', 'completion_date', 'updated_at'])
            return True
        return False
    
    def cancel(self, reason, cancelled_by_user=None):
        """Cancel a booking"""
        if self.status not in ['completed', 'cancelled', 'disputed']:
            self.status = 'cancelled'
            self.cancellation_reason = reason
            self.cancelled_by = cancelled_by_user
            self.cancellation_date = models.functions.Now()
            self.save(update_fields=['status', 'cancellation_reason', 'cancelled_by', 'cancellation_date', 'updated_at'])
            return True
        return False
        
    def reschedule(self, new_date, new_start_time=None, new_end_time=None, reason=None):
        """Reschedule a booking to a new date and time"""
        if self.status not in ['completed', 'cancelled', 'disputed']:
            if not self.is_rescheduled:
                self.original_booking_date = models.functions.Concat(
                    models.functions.Cast('booking_date', models.CharField()),
                    models.Value(' '),
                    models.functions.Cast('start_time', models.CharField())
                )
                self.is_rescheduled = True
            
            self.rescheduled_date = new_date
            self.booking_date = new_date
            
            if new_start_time:
                self.start_time = new_start_time
            
            if new_end_time:
                self.end_time = new_end_time
                
            self.rescheduled_count += 1
            self.rescheduled_reason = reason
            
            self.save()
            return True
        return False
        
    def add_review(self, rating, review_text):
        """Add a review and rating to a completed booking"""
        if self.status == 'completed' and self.rating is None:
            self.rating = rating
            self.review = review_text
            self.save(update_fields=['rating', 'review', 'updated_at'])
            return True
        return False

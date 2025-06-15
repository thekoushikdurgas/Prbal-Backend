from django.db import models
from django.conf import settings
import uuid
from services.models import Service
from bookings.models import Booking
from django.utils import timezone

def review_image_path(instance, filename):
    # Generate a unique path for storing review images
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"review_images/{instance.review.id}/{filename}"

# Create your models here.
class Review(models.Model):
    """Manages service reviews and ratings provided by users"""
    
    # Primary key and relationship fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='reviews', help_text='The booking this review is for')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reviews', help_text='The service being reviewed')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_given', null=True, help_text='Customer who left the review')
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received', null=True, help_text='Service provider being reviewed')
    
    # Rating fields
    rating = models.DecimalField(max_digits=3, decimal_places=1, help_text='Overall rating of the service')
    rating_breakdown = models.JSONField(null=True, blank=True, help_text='Detailed breakdown of ratings (e.g., punctuality, quality)')
    
    # Review content
    comment = models.TextField(help_text='Text comment of the review')
    
    # Verification and visibility
    is_verified = models.BooleanField(default=False, help_text='Flag indicating if the review is verified')
    is_public = models.BooleanField(default=True, help_text='Whether the review is publicly visible')
    
    # Provider response
    provider_response = models.TextField(blank=True, null=True, help_text="Provider's text response to the review")
    provider_response_date = models.DateTimeField(null=True, blank=True, help_text="Timestamp of the provider's response")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
    
    def __str__(self):
        return f"{self.client.username}'s review for {self.service.title}"
    
    def add_provider_response(self, response_text):
        """Add or update provider response to this review"""
        self.provider_response = response_text
        self.provider_response_date = timezone.now()
        self.save(update_fields=['provider_response', 'provider_response_date', 'updated_at'])
        return True
        
    def verify(self):
        """Mark the review as verified"""
        self.is_verified = True
        self.save(update_fields=['is_verified', 'updated_at'])
        return True
        
    def update_rating(self, overall_rating, breakdown=None):
        """Update the rating and optionally the rating breakdown"""
        self.rating = overall_rating
        if breakdown:
            self.rating_breakdown = breakdown
        self.save(update_fields=['rating', 'rating_breakdown' if breakdown else 'rating', 'updated_at'])
        return True

class ReviewImage(models.Model):
    """Model for storing images associated with reviews"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=review_image_path, help_text='Image uploaded with the review')
    caption = models.CharField(max_length=100, blank=True, help_text='Optional caption for the image')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"Image for {self.review}"

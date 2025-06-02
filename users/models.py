from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.search import SearchVector
from django.contrib.postgres.indexes import GinIndex
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Create your models here.
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('provider', 'Service Provider'),
        ('admin', 'Administrator'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    # Email is already provided by AbstractUser but we add unique constraint
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    # Verification fields
    is_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    # Profile fields
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    # Provider specific fields
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0, null=True, blank=True)
    total_bookings = models.IntegerField(default=0)
    skills = models.JSONField(default=dict, blank=True, null=True)
    # User preferences and financial info
    preferences = models.JSONField(default=dict, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    search_vector = SearchVectorField(null=True, editable=False, blank=True) # blank=True for initial migration
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            GinIndex(fields=['search_vector'], name='user_search_vector_idx'),
        ]
        
    def __str__(self):
        return self.username
        
    @property
    def name(self):
        """Returns the user's full name for API compatibility"""
        return self.get_full_name() or self.username


@receiver(post_save, sender=User)
def update_user_search_vector(sender, instance, **kwargs):
    # Using .filter().update() avoids recursion by not calling instance.save() again
    # It also handles the case where the instance might be new (kwargs['created'] is True)
    # or existing.
    User.objects.filter(pk=instance.pk).update(search_vector=SearchVector(
        'username', 'email', 'first_name', 'last_name', 'phone_number',
        config='english'  # Or your project's primary language
    ))


class Pass(models.Model):
    user_passing = models.ForeignKey(User, related_name='passes_made', on_delete=models.CASCADE)
    user_passed = models.ForeignKey(User, related_name='passes_received', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_passing', 'user_passed')
        verbose_name = _('Pass')
        verbose_name_plural = _('Passes')

    def __str__(self):
        return f"{self.user_passing.username} passed on {self.user_passed.username}"


class AccessToken(models.Model):
    DEVICE_TYPE_CHOICES = (
        ('web', 'Web Browser'),
        ('mobile', 'Mobile App'),
        ('tablet', 'Tablet'),
        ('desktop', 'Desktop App'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, related_name='access_tokens', on_delete=models.CASCADE)
    token_jti = models.CharField(max_length=255, unique=True, help_text="JWT token ID")
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPE_CHOICES, default='web')
    device_name = models.CharField(max_length=255, blank=True, null=True, help_text="User agent or device identifier")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    last_refreshed_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Access Token')
        verbose_name_plural = _('Access Tokens')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Token for {self.user.username} on {self.device_type} created at {self.created_at}"
    
    def refresh(self):
        """Update the refresh timestamp"""
        self.last_refreshed_at = timezone.now()
        self.save(update_fields=['last_refreshed_at'])

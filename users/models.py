from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
import uuid
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.search import SearchVector
from django.contrib.postgres.indexes import GinIndex
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

class UserManager(BaseUserManager):
    def create_user(self, username, email, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, **extra_fields)

# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('provider', 'Service Provider'),
        ('admin', 'Administrator'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    
    # PIN Authentication fields
    pin = models.CharField(max_length=128, help_text=_('4-digit PIN for authentication (hashed)'))
    pin_created_at = models.DateTimeField(auto_now_add=True)
    pin_updated_at = models.DateTimeField(auto_now=True)
    failed_pin_attempts = models.IntegerField(default=0)
    pin_locked_until = models.DateTimeField(blank=True, null=True)
    
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
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            GinIndex(fields=['search_vector'], name='user_search_vector_idx'),
        ]
        
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    def get_user_type_display(self):
        """Return the display name for user type."""
        return dict(self.USER_TYPE_CHOICES).get(self.user_type, self.user_type)
        
    @property
    def name(self):
        """Returns the user's full name for API compatibility"""
        return self.get_full_name() or self.username
    
    def set_pin(self, raw_pin):
        """Set the PIN for the user (stores as hash for security)"""
        if len(str(raw_pin)) != 4 or not str(raw_pin).isdigit():
            raise ValueError(_('PIN must be exactly 4 digits'))
        self.pin = make_password(str(raw_pin))
        self.pin_updated_at = timezone.now()
        self.failed_pin_attempts = 0
        self.pin_locked_until = None
    
    def check_pin(self, raw_pin):
        """Check if the provided PIN matches the stored PIN"""
        if self.is_pin_locked():
            return False
        
        # Check if PIN matches
        is_correct = check_password(str(raw_pin), self.pin)
        
        if is_correct:
            # Reset failed attempts on successful PIN entry
            self.failed_pin_attempts = 0
            self.pin_locked_until = None
            self.save(update_fields=['failed_pin_attempts', 'pin_locked_until'])
        else:
            # Increment failed attempts
            self.failed_pin_attempts += 1
            # Lock PIN after 5 failed attempts for 30 minutes
            if self.failed_pin_attempts >= 5:
                self.pin_locked_until = timezone.now() + timezone.timedelta(minutes=30)
            self.save(update_fields=['failed_pin_attempts', 'pin_locked_until'])
        
        return is_correct
    
    def is_pin_locked(self):
        """Check if PIN is currently locked due to failed attempts"""
        if self.pin_locked_until and timezone.now() < self.pin_locked_until:
            return True
        elif self.pin_locked_until and timezone.now() >= self.pin_locked_until:
            # Auto-unlock if lock time has passed
            self.failed_pin_attempts = 0
            self.pin_locked_until = None
            self.save(update_fields=['failed_pin_attempts', 'pin_locked_until'])
        return False
    
    def get_pin_lock_remaining_time(self):
        """Get remaining lock time in minutes"""
        if self.is_pin_locked():
            remaining = self.pin_locked_until - timezone.now()
            return max(0, int(remaining.total_seconds() / 60))
        return 0


@receiver(post_save, sender=User)
def update_user_search_vector(sender, instance, created, **kwargs):
    # Set default PIN for new users
    if created and not instance.pin:
        instance.set_pin('1234')
        instance.save(update_fields=['pin', 'pin_updated_at', 'failed_pin_attempts', 'pin_locked_until'])
    
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

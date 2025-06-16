import os
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
from prbal_project import settings
from django.db import models
from django.conf import settings
import uuid
import os
from django.utils import timezone


def profile_picture_path(instance, filename):
    """Generate secure path for profile pictures"""
    from .utils import secure_upload_path
    return secure_upload_path(instance, filename, 'profile_pictures')


def verification_document_path(instance, filename):
    """Generate a secure, unique path for storing verification documents"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"verification_documents/{instance.user.id}/{instance.verification_type}/{filename}"


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
    
    # Profile fields - Fixed to use proper path function
    profile_picture = models.ImageField(upload_to=profile_picture_path, blank=True, null=True)
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
    
    def profile_picture_url(self, request=None):
        """
        Get the full URL for the profile picture with absolute domain
        
        Args:
            request: HTTP request object for building absolute URI
            
        Returns:
            str: Full URL with domain or relative URL if no request provided
        """
        from .utils import get_media_url, get_absolute_media_url
        
        if not self.profile_picture:
            return None
            
        # Get the relative URL first
        relative_url = get_media_url(self.profile_picture.url)
        
        # Get absolute URL with domain
        return get_absolute_media_url(relative_url, request)
    
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


# Create your models here.
class Verification(models.Model):
    """Manages the comprehensive user verification process"""
    
    VERIFICATION_TYPE_CHOICES = (
        ('identity', 'Identity Verification'),
        ('address', 'Address Verification'),
        ('professional', 'Professional Certification'),
        ('educational', 'Educational Verification'),
        ('background', 'Background Check'),
        ('business', 'Business Registration'),
        ('banking', 'Banking Information'),
        ('other', 'Other Verification'),
    )
    
    STATUS_CHOICES = (
        ('unverified', 'Unverified'),
        ('pending', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )
    
    DOCUMENT_TYPE_CHOICES = (
        # Identity documents
        ('national_id', 'National ID Card'),
        ('passport', 'Passport'),
        ('drivers_license', 'Driver\'s License'),
        ('voter_id', 'Voter ID Card'),
        ('aadhaar', 'Aadhaar Card'),
        ('pan_card', 'PAN Card'),
        
        # Address documents
        ('utility_bill', 'Utility Bill'),
        ('bank_statement', 'Bank Statement'),
        ('rental_agreement', 'Rental Agreement'),
        ('property_tax', 'Property Tax Receipt'),
        
        # Professional documents
        ('professional_cert', 'Professional Certificate'),
        ('business_license', 'Business License'),
        ('employment_contract', 'Employment Contract'),
        ('tax_document', 'Tax Document'),
        
        # Educational documents
        ('degree', 'Degree Certificate'),
        ('transcript', 'Academic Transcript'),
        ('course_completion', 'Course Completion Certificate'),
        
        # Other
        ('other', 'Other Document'),
    )
    
    # Primary key and relationship fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the verification entry")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verifications', help_text="User being verified")
    
    # Verification details
    verification_type = models.CharField(max_length=30, choices=VERIFICATION_TYPE_CHOICES, help_text="Type of verification")
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES, default='other', help_text="Type of document submitted")
    document_url = models.FileField(upload_to=verification_document_path, null=True, blank=True, help_text="Uploaded verification document")
    document_back_url = models.FileField(upload_to=verification_document_path, blank=True, null=True, help_text="Back side of document if applicable")
    document_link = models.URLField(max_length=255, blank=True, null=True, help_text="External link to verification document")
    document_number = models.CharField(max_length=50, blank=True, help_text="Document number for reference")
    
    # Status and feedback
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Current status of verification")
    verification_notes = models.TextField(blank=True, help_text="Internal notes about the verification process")
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection if applicable")
    
    # Administrative tracking
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='verifications_processed', help_text="Admin who processed this verification")
    
    # Timestamps
    verified_at = models.DateTimeField(null=True, blank=True, help_text="When the verification was approved")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When the verification expires")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the verification was submitted")
    updated_at = models.DateTimeField(auto_now=True, help_text="When the verification was last updated")
    
    # External integration
    external_reference_id = models.CharField(max_length=100, blank=True, help_text="Reference ID from external verification service")
    metadata = models.JSONField(default=dict, blank=True, null=True, help_text="Additional metadata related to verification")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Verification'
        verbose_name_plural = 'Verifications'
        unique_together = ['user', 'verification_type', 'document_type']
    
    def __str__(self):
        return f"{self.user.username}'s {self.get_verification_type_display()} verification"
    
    def mark_as_in_progress(self, notes=None, admin=None):
        """Mark this verification as in progress with optional notes"""
        if not self.status == 'pending':
            raise ValueError("Only pending verifications can be marked as in progress")
            
        self.status = 'in_progress'
        if notes:
            self.verification_notes = notes
        if admin:
            self.verified_by = admin
        self.save(update_fields=['status', 'verification_notes', 'verified_by', 'updated_at'])
        return True

    def mark_as_verified(self, verified_by=None, notes=None, expiry_days=365):
        """Mark this verification as verified"""
        if self.status not in ['pending', 'in_progress']:
            raise ValueError("Only pending or in-progress verifications can be marked as verified")
            
        self.status = 'verified'
        self.verified_at = timezone.now()
        self.expires_at = self.verified_at + timezone.timedelta(days=expiry_days)
        
        if verified_by:
            self.verified_by = verified_by
        if notes:
            self.verification_notes = notes
            
        # Update user's verification status based on verification type
        if self.verification_type == 'identity':
            self.user.is_verified = True
            self.user.save(update_fields=['is_verified'])
            
        self.save()
        return True

    def mark_as_rejected(self, reason, verified_by=None):
        """Mark this verification as rejected with a reason"""
        if self.status not in ['pending', 'in_progress']:
            raise ValueError("Only pending or in-progress verifications can be rejected")
            
        if not reason:
            raise ValueError("Rejection reason is required")
            
        self.status = 'rejected'
        self.rejection_reason = reason
        if verified_by:
            self.verified_by = verified_by
        self.save()
        return True

    def cancel(self, cancelled_by=None):
        """Cancel a pending verification"""
        if self.status != 'pending':
            raise ValueError("Only pending verifications can be cancelled")
            
        if cancelled_by and cancelled_by != self.user:
            raise ValueError("Only the verification owner can cancel it")
            
        self.status = 'unverified'
        self.save(update_fields=['status', 'updated_at'])
        return True

    def is_expired(self):
        """Check if this verification is expired"""
        if self.expires_at and self.expires_at < timezone.now():
            # Auto-update status if expired but not marked as such
            if self.status == 'verified':
                self.status = 'expired'
                self.save(update_fields=['status', 'updated_at'])
            return True
        return False
    
    def mark_as_unverified(self):
        """Reset verification to unverified state"""
        if self.status in ['rejected', 'expired']:
            self.status = 'unverified'
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
        
    @property
    def document_filename(self):
        """Return just the filename of the document, not the full path"""
        return os.path.basename(self.document_url.name) if self.document_url else None

from django.db import models
from django.conf import settings
import uuid
import os
from django.utils import timezone

def verification_document_path(instance, filename):
    # Generate a secure, unique path for storing verification documents
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"verification_documents/{instance.user.id}/{instance.verification_type}/{filename}"

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
    
    def mark_as_in_progress(self, notes=None):
        """Mark this verification as in progress with optional notes"""
        if self.status in ['unverified', 'pending']:
            self.status = 'in_progress'
            if notes:
                self.verification_notes = notes
            self.save(update_fields=['status', 'verification_notes' if notes else 'status', 'updated_at'])
            return True
        return False
    
    def mark_as_verified(self, verified_by=None, notes=None, expiry_days=365):
        """Mark this verification as verified"""
        if self.status in ['pending', 'in_progress']:
            self.status = 'verified'
            self.verified_at = timezone.now()
            # Set expiration date from verification date
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
        return False
    
    def mark_as_rejected(self, reason, verified_by=None):
        """Mark this verification as rejected with a reason"""
        if self.status in ['pending', 'in_progress']:
            self.status = 'rejected'
            self.rejection_reason = reason
            if verified_by:
                self.verified_by = verified_by
            self.save()
            return True
        return False
    
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

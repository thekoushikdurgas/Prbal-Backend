from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
# For future GeoDjango implementation:
# from django.contrib.gis.db import models as gis_models

# Create your models here.
class ServiceCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    icon_url = models.URLField(max_length=500, blank=True, null=True, help_text="External icon URL")
    sort_order = models.PositiveIntegerField(default=0, help_text="Order for displaying categories")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Service Categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class ServiceSubCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    icon_url = models.URLField(max_length=500, blank=True, null=True, help_text="External icon URL")
    sort_order = models.PositiveIntegerField(default=0, help_text="Order for displaying subcategories within category")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Service SubCategories'
        ordering = ['category__sort_order', 'category__name', 'sort_order', 'name']
        unique_together = ['category', 'name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"

class ServiceImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey('Service', on_delete=models.CASCADE, related_name='service_images')
    image = models.ImageField(upload_to='service_images/')
    description = models.CharField(max_length=255, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Service Images'
        
    def __str__(self):
        return f"Image for {self.service.name}"

class Service(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('pending', 'Pending Approval'),
        ('inactive', 'Inactive'),
    )
    
    CURRENCY_CHOICES = (
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    )
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)  # Renamed from title for API compatibility
    description = models.TextField()
    
    # Categorization
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    subcategories = models.ManyToManyField(ServiceSubCategory, related_name='services', blank=True)
    tags = models.JSONField(default=list, blank=True, null=True)
    
    # Pricing
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    pricing_options = models.JSONField(default=dict, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    
    # Booking constraints
    min_hours = models.PositiveIntegerField(default=1)
    max_hours = models.PositiveIntegerField(default=8)
    
    # Availability
    availability = models.JSONField(default=dict, blank=True, null=True)
    
    # Location
    # For future: location = gis_models.PointField(geography=True, blank=True, null=True)
    # Currently using separate fields for coordinates:
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Additional info
    required_tools = models.JSONField(default=list, blank=True, null=True)
    
    # Status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def title(self):
        """For backward compatibility"""
        return self.name
    
    @property
    def price(self):
        """For backward compatibility"""
        return self.base_price
        
    @property
    def hourly_rate(self):
        """For backward compatibility"""
        return self.base_price
    
    @property
    def images(self):
        """Returns a list of image URLs"""
        return [img.image.url for img in self.service_images.all()]
    
    def set_coordinates(self, latitude, longitude):
        """Helper method to set coordinates"""
        self.latitude = latitude
        self.longitude = longitude
        self.save()


class ServiceRequest(models.Model):
    """
    Model for customers to request services that may not exist yet.
    This allows customers to express interest in services they need.
    Providers can browse these requests and create matching services.
    """
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )
    
    URGENCY_CHOICES = (
        ('low', 'Low - Within a month'),
        ('medium', 'Medium - Within a week'),
        ('high', 'High - Within 48 hours'),
        ('urgent', 'Urgent - Within 24 hours'),
    )
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_requests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Categorization
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='service_requests')
    subcategories = models.ManyToManyField(ServiceSubCategory, related_name='service_requests', blank=True)
    
    # Budget and timing
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=Service.CURRENCY_CHOICES, default='INR')
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='medium')
    requested_date_time = models.DateTimeField(null=True, blank=True)
    
    # Location
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Status fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_featured = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Provider who accepted the request (if any)
    assigned_provider = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        related_name='assigned_service_requests',
        null=True, 
        blank=True
    )
    
    # Service created in response to this request (if any)
    fulfilled_by_service = models.ForeignKey(
        Service, 
        on_delete=models.SET_NULL, 
        related_name='originated_from_request',
        null=True, 
        blank=True
    )
    
    # Additional requirements or preferences
    requirements = models.JSONField(default=dict, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Service Request'
        verbose_name_plural = 'Service Requests'
    
    def __str__(self):
        return f"{self.title} by {self.customer.username}"
    
    def save(self, *args, **kwargs):
        # Set expiration date if not already set
        if not self.expires_at:
            # Default expiration is 30 days from creation
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if the request has expired"""
        return timezone.now() > self.expires_at
    
    def mark_as_expired(self):
        """Mark the request as expired"""
        self.status = 'expired'
        self.save()
    
    def assign_provider(self, provider):
        """Assign a provider to this request"""
        self.assigned_provider = provider
        self.status = 'in_progress'
        self.save()
    
    def mark_as_fulfilled(self, service=None):
        """Mark the request as fulfilled, optionally linking to a service"""
        self.status = 'fulfilled'
        if service:
            self.fulfilled_by_service = service
        self.save()

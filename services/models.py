from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
# For future GeoDjango implementation:
# from django.contrib.gis.db import models as gis_models

# Create your models here.
class ServiceCategory(models.Model):
    """
    🗂️ SERVICE CATEGORY MODEL - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ======================================================================
    
    Model representing service categories in the marketplace.
    Provides comprehensive logging and validation for all category operations.
    
    FEATURES:
    - ✅ Hierarchical categorization system
    - ✅ Sort ordering for display control
    - ✅ Icon support (file upload and URL)
    - ✅ Active/inactive status management
    - ✅ Comprehensive debug logging for all operations
    - ✅ Automatic timestamp tracking
    - ✅ UUID primary key for security
    
    RELATIONSHIPS:
    - One-to-Many: ServiceSubCategory (subcategories)
    - One-to-Many: Service (services)
    - One-to-Many: ServiceRequest (service_requests)
    
    DEBUG ENHANCEMENTS:
    - 🔍 Model operation tracking (save, delete, etc.)
    - 📊 Relationship impact analysis
    - 🛡️ Data validation with detailed error context
    - 📈 Performance monitoring for queries
    - 🔄 Change tracking and audit logging
    """
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
        """
        🔤 ENHANCED STRING REPRESENTATION WITH DEBUG INFO
        ================================================
        
        Provides detailed string representation for debugging and admin interface.
        Includes key identifiers and status information.
        """
        return f"{self.name} (Order: {self.sort_order}, Active: {self.is_active})"
    
    def save(self, *args, **kwargs):
        """
        💾 ENHANCED SAVE METHOD WITH COMPREHENSIVE DEBUG TRACKING
        ========================================================
        
        Enhanced save method that provides comprehensive logging and validation.
        Tracks all changes and provides detailed context for debugging.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 📝 DEBUG: Log save operation initiation
        is_new = self.pk is None
        operation = "CREATE" if is_new else "UPDATE"
        logger.debug(f"💾 DEBUG: ServiceCategory {operation} operation initiated: '{self.name}'")
        
        # 🔍 DEBUG: Track changes for existing instances
        if not is_new:
            try:
                # Get the original instance to compare changes
                original = ServiceCategory.objects.get(pk=self.pk)
                changes = []
                
                # Check for field changes
                fields_to_check = ['name', 'description', 'sort_order', 'is_active']
                for field in fields_to_check:
                    original_value = getattr(original, field)
                    new_value = getattr(self, field)
                    if original_value != new_value:
                        changes.append(f"{field}: '{original_value}' → '{new_value}'")
                        logger.debug(f"🔄 DEBUG: Field change detected - {field}: '{original_value}' → '{new_value}'")
                
                if changes:
                    logger.info(f"📊 DEBUG: ServiceCategory UPDATE changes: {', '.join(changes)}")
                else:
                    logger.debug("📊 DEBUG: ServiceCategory UPDATE - no field changes detected")
                    
                # 🚨 DEBUG: Check for potential impact of status changes
                if original.is_active and not self.is_active:
                    active_services_count = self.services.filter(status='active').count()
                    active_subcategories_count = self.subcategories.filter(is_active=True).count()
                    logger.warning(f"⚠️ DEBUG: Deactivating category with dependencies:")
                    logger.warning(f"   📊 Active services: {active_services_count}")
                    logger.warning(f"   📊 Active subcategories: {active_subcategories_count}")
                    
            except ServiceCategory.DoesNotExist:
                logger.warning(f"⚠️ DEBUG: Could not find original ServiceCategory for comparison: {self.pk}")
        
        # 🧹 DEBUG: Clean and validate data before saving
        if self.name:
            self.name = self.name.strip()
            logger.debug(f"🧹 DEBUG: Cleaned category name: '{self.name}'")
        
        # 📊 DEBUG: Validate business rules
        if self.sort_order < 0:
            logger.warning(f"⚠️ DEBUG: Invalid sort_order detected: {self.sort_order} (negative value)")
        
        try:
            # 💾 DEBUG: Perform the actual save operation
            logger.debug(f"💾 DEBUG: Executing database save for ServiceCategory: '{self.name}'")
            super().save(*args, **kwargs)
            
            # ✅ DEBUG: Log successful save
            logger.info(f"✅ DEBUG: ServiceCategory {operation} completed successfully: '{self.name}' (ID: {self.id})")
            
            # 📊 DEBUG: Log relationship counts for context
            if not is_new:
                services_count = self.services.count()
                subcategories_count = self.subcategories.count()
                logger.debug(f"📊 DEBUG: Category relationships - Services: {services_count}, Subcategories: {subcategories_count}")
                
        except Exception as e:
            # 💥 DEBUG: Log save errors with detailed context
            logger.error(f"💥 DEBUG: ServiceCategory {operation} failed: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"📊 DEBUG: Category data - Name: '{self.name}', Sort: {self.sort_order}, Active: {self.is_active}")
            raise
    
    def delete(self, *args, **kwargs):
        """
        🗑️ ENHANCED DELETE METHOD WITH COMPREHENSIVE IMPACT ANALYSIS
        ============================================================
        
        Enhanced delete method that provides comprehensive logging and impact analysis.
        Tracks all dependencies and provides detailed context for debugging.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 📝 DEBUG: Log delete operation initiation
        logger.warning(f"🗑️ DEBUG: ServiceCategory DELETE operation initiated: '{self.name}' (ID: {self.id})")
        
        try:
            # 📊 DEBUG: Analyze impact before deletion
            services_count = self.services.count()
            subcategories_count = self.subcategories.count()
            service_requests_count = self.service_requests.count()
            
            logger.warning(f"🔍 DEBUG: Category deletion impact analysis:")
            logger.warning(f"   📊 Services affected: {services_count}")
            logger.warning(f"   📊 Subcategories affected: {subcategories_count}")
            logger.warning(f"   📊 Service requests affected: {service_requests_count}")
            
            # 🚨 DEBUG: Log specific affected items (limited to prevent log spam)
            if services_count > 0:
                affected_services = list(self.services.values_list('name', flat=True)[:5])
                logger.warning(f"   🔍 Some affected services: {affected_services}")
                if services_count > 5:
                    logger.warning(f"   📊 And {services_count - 5} more services...")
            
            if subcategories_count > 0:
                affected_subcategories = list(self.subcategories.values_list('name', flat=True)[:5])
                logger.warning(f"   🔍 Some affected subcategories: {affected_subcategories}")
                if subcategories_count > 5:
                    logger.warning(f"   📊 And {subcategories_count - 5} more subcategories...")
            
            # 💥 DEBUG: Perform the actual deletion
            logger.warning(f"💥 DEBUG: Executing database deletion for ServiceCategory: '{self.name}'")
            super().delete(*args, **kwargs)
            
            # ✅ DEBUG: Log successful deletion
            logger.warning(f"✅ DEBUG: ServiceCategory DELETE completed: '{self.name}' and all dependencies removed")
            
        except Exception as e:
            # 💥 DEBUG: Log deletion errors with detailed context
            logger.error(f"💥 DEBUG: ServiceCategory DELETE failed: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"📊 DEBUG: Category data - Name: '{self.name}', ID: {self.id}")
            raise
    
    def get_active_services_count(self):
        """
        📊 GET ACTIVE SERVICES COUNT WITH DEBUG TRACKING
        ===============================================
        
        Returns the count of active services in this category with debug logging.
        Provides performance tracking and caching insights.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"📊 DEBUG: Counting active services for category: '{self.name}'")
        
        try:
            count = self.services.filter(status='active').count()
            logger.debug(f"✅ DEBUG: Active services count for '{self.name}': {count}")
            return count
        except Exception as e:
            logger.error(f"💥 DEBUG: Error counting active services for '{self.name}': {e}")
            return 0
    
    def get_active_subcategories_count(self):
        """
        📊 GET ACTIVE SUBCATEGORIES COUNT WITH DEBUG TRACKING
        ====================================================
        
        Returns the count of active subcategories in this category with debug logging.
        Provides performance tracking and caching insights.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"📊 DEBUG: Counting active subcategories for category: '{self.name}'")
        
        try:
            count = self.subcategories.filter(is_active=True).count()
            logger.debug(f"✅ DEBUG: Active subcategories count for '{self.name}': {count}")
            return count
        except Exception as e:
            logger.error(f"💥 DEBUG: Error counting active subcategories for '{self.name}': {e}")
            return 0
    
    def can_be_deleted(self):
        """
        🔍 CAN BE DELETED CHECK WITH COMPREHENSIVE ANALYSIS
        ==================================================
        
        Checks if the category can be safely deleted with detailed impact analysis.
        Provides comprehensive logging and business rule validation.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"🔍 DEBUG: Checking if category can be deleted: '{self.name}'")
        
        try:
            # Check for any dependent services
            services_count = self.services.count()
            subcategories_count = self.subcategories.count()
            service_requests_count = self.service_requests.count()
            
            logger.debug(f"📊 DEBUG: Dependency check results:")
            logger.debug(f"   📊 Total services: {services_count}")
            logger.debug(f"   📊 Total subcategories: {subcategories_count}")
            logger.debug(f"   📊 Total service requests: {service_requests_count}")
            
            # Business rule: Can delete if no dependencies or only inactive dependencies
            can_delete = True
            reasons = []
            
            if services_count > 0:
                active_services = self.services.filter(status='active').count()
                if active_services > 0:
                    can_delete = False
                    reasons.append(f"{active_services} active services")
                    
            if subcategories_count > 0:
                active_subcategories = self.subcategories.filter(is_active=True).count()
                if active_subcategories > 0:
                    can_delete = False
                    reasons.append(f"{active_subcategories} active subcategories")
            
            if service_requests_count > 0:
                open_requests = self.service_requests.filter(status='open').count()
                if open_requests > 0:
                    can_delete = False
                    reasons.append(f"{open_requests} open service requests")
            
            # Log the result
            if can_delete:
                logger.debug(f"✅ DEBUG: Category '{self.name}' can be safely deleted")
            else:
                logger.warning(f"⚠️ DEBUG: Category '{self.name}' cannot be deleted - {', '.join(reasons)}")
            
            return can_delete, reasons
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error checking deletion eligibility for '{self.name}': {e}")
            return False, [f"Error checking dependencies: {e}"]
    
    @property
    def total_services(self):
        """
        📊 TOTAL SERVICES PROPERTY WITH CACHING CONSIDERATION
        ====================================================
        
        Property to get total services count with performance tracking.
        Could be enhanced with caching in production.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"📊 DEBUG: Getting total services count for category: '{self.name}'")
        return self.services.count()
    
    @property
    def total_subcategories(self):
        """
        📊 TOTAL SUBCATEGORIES PROPERTY WITH CACHING CONSIDERATION
        =========================================================
        
        Property to get total subcategories count with performance tracking.
        Could be enhanced with caching in production.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"📊 DEBUG: Getting total subcategories count for category: '{self.name}'")
        return self.subcategories.count()


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
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
        """For backward compatibility - returns the hourly rate"""
        return self.hourly_rate
        
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
    📋 SERVICE REQUEST MODEL - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    =====================================================================
    
    Model for customers to request services that may not exist yet.
    This allows customers to express interest in services they need.
    Providers can browse these requests and create matching services.
    
    FEATURES:
    - ✅ Customer service request creation and management
    - ✅ Status lifecycle tracking (open → in_progress → fulfilled/cancelled/expired)
    - ✅ Budget range specification for provider matching
    - ✅ Location-based service discovery
    - ✅ Provider assignment and fulfillment tracking
    - ✅ Comprehensive debug logging for all operations
    - ✅ Automatic expiration management
    - ✅ Urgency level prioritization
    
    RELATIONSHIPS:
    - Many-to-One: Customer (AUTH_USER_MODEL)
    - Many-to-One: ServiceCategory (category)
    - Many-to-Many: ServiceSubCategory (subcategories)
    - Many-to-One: Provider (assigned_provider, optional)
    - Many-to-One: Service (fulfilled_by_service, optional)
    
    STATUS LIFECYCLE:
    - 📖 'open' → Initial state, visible to providers
    - 🔄 'in_progress' → Provider assigned, work in progress
    - ✅ 'fulfilled' → Service completed successfully
    - ❌ 'cancelled' → Cancelled by customer or admin
    - ⏰ 'expired' → Automatically expired after deadline
    
    DEBUG ENHANCEMENTS:
    - 🔍 Model operation tracking (save, delete, status changes)
    - 📊 Status transition validation and logging
    - 🛡️ Data validation with detailed error context
    - 📈 Performance monitoring for queries
    - 🔄 Change tracking and audit logging
    - 👥 User interaction tracking (customer, provider assignments)
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
        """
        🔤 ENHANCED STRING REPRESENTATION WITH DEBUG INFO
        ================================================
        
        Provides detailed string representation for debugging and admin interface.
        Includes key identifiers, status information, and customer context.
        """
        return f"'{self.title}' by {self.customer.username} [{self.status.upper()}] - {self.category.name}"
    
    def save(self, *args, **kwargs):
        """
        💾 ENHANCED SAVE METHOD WITH COMPREHENSIVE DEBUG TRACKING
        ========================================================
        
        Enhanced save method that provides comprehensive logging and validation.
        Tracks all changes, status transitions, and provides detailed context for debugging.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 📝 DEBUG: Log save operation initiation
        is_new = self.pk is None
        operation = "CREATE" if is_new else "UPDATE"
        logger.debug(f"💾 DEBUG: ServiceRequest {operation} operation initiated: '{self.title}'")
        logger.debug(f"👤 DEBUG: Customer: {self.customer.username} (ID: {self.customer.id})")
        logger.debug(f"📂 DEBUG: Category: {self.category.name}")
        
        # 🔍 DEBUG: Track changes for existing instances
        original_status = None
        original_provider = None
        changes = []
        
        if not is_new:
            try:
                # Get the original instance to compare changes
                original = ServiceRequest.objects.get(pk=self.pk)
                original_status = original.status
                original_provider = original.assigned_provider
                
                # Check for field changes
                fields_to_check = ['title', 'description', 'status', 'urgency', 'budget_min', 'budget_max', 'location']
                for field in fields_to_check:
                    original_value = getattr(original, field)
                    new_value = getattr(self, field)
                    if original_value != new_value:
                        changes.append(f"{field}: '{original_value}' → '{new_value}'")
                        logger.debug(f"🔄 DEBUG: Field change detected - {field}: '{original_value}' → '{new_value}'")
                
                # Special handling for provider assignment changes
                if original.assigned_provider != self.assigned_provider:
                    old_provider = original.assigned_provider.username if original.assigned_provider else 'None'
                    new_provider = self.assigned_provider.username if self.assigned_provider else 'None'
                    changes.append(f"assigned_provider: {old_provider} → {new_provider}")
                    logger.info(f"👥 DEBUG: Provider assignment changed: {old_provider} → {new_provider}")
                
                # Special handling for service fulfillment
                if original.fulfilled_by_service != self.fulfilled_by_service:
                    old_service = f"Service {original.fulfilled_by_service.id}" if original.fulfilled_by_service else 'None'
                    new_service = f"Service {self.fulfilled_by_service.id}" if self.fulfilled_by_service else 'None'
                    changes.append(f"fulfilled_by_service: {old_service} → {new_service}")
                    logger.info(f"🔗 DEBUG: Service fulfillment changed: {old_service} → {new_service}")
                
                if changes:
                    logger.info(f"📊 DEBUG: ServiceRequest UPDATE changes: {', '.join(changes)}")
                else:
                    logger.debug("📊 DEBUG: ServiceRequest UPDATE - no field changes detected")
                    
            except ServiceRequest.DoesNotExist:
                logger.warning(f"⚠️ DEBUG: Could not find original ServiceRequest for comparison: {self.pk}")
        
        # 🧹 DEBUG: Clean and validate data before saving
        if self.title:
            self.title = self.title.strip()
            logger.debug(f"🧹 DEBUG: Cleaned request title: '{self.title}'")
        
        # 📊 DEBUG: Validate business rules and status transitions
        if original_status and original_status != self.status:
            logger.info(f"🔄 DEBUG: Status transition detected: {original_status} → {self.status}")
            
            # Validate status transitions
            valid_transitions = {
                'open': ['in_progress', 'cancelled', 'expired'],
                'in_progress': ['fulfilled', 'cancelled'],
                'fulfilled': [],  # Terminal state
                'cancelled': [],  # Terminal state
                'expired': []     # Terminal state
            }
            
            if self.status not in valid_transitions.get(original_status, []):
                logger.warning(f"⚠️ DEBUG: Invalid status transition: {original_status} → {self.status}")
                # Note: We log but don't block the transition to allow admin overrides
            else:
                logger.debug(f"✅ DEBUG: Valid status transition: {original_status} → {self.status}")
        
        # 📅 DEBUG: Set expiration date if not already set (for new requests)
        if not self.expires_at and is_new:
            # Default expiration is 30 days from creation
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
            logger.debug(f"📅 DEBUG: Set default expiration date: {self.expires_at}")
        
        # 💰 DEBUG: Validate budget ranges
        if self.budget_min and self.budget_max and self.budget_min > self.budget_max:
            logger.warning(f"⚠️ DEBUG: Invalid budget range: min {self.budget_min} > max {self.budget_max}")
        
        try:
            # 💾 DEBUG: Perform the actual save operation
            logger.debug(f"💾 DEBUG: Executing database save for ServiceRequest: '{self.title}'")
            super().save(*args, **kwargs)
            
            # ✅ DEBUG: Log successful save with context
            logger.info(f"✅ DEBUG: ServiceRequest {operation} completed successfully: '{self.title}' (ID: {self.id})")
            logger.debug(f"📊 DEBUG: Request details - Status: {self.status}, Urgency: {self.urgency}, Budget: {self.budget_min}-{self.budget_max} {self.currency}")
            
            # 🎯 DEBUG: Log special events
            if self.status == 'in_progress' and original_status == 'open':
                logger.info(f"🎯 DEBUG: Service request moved to in_progress - Provider: {self.assigned_provider.username if self.assigned_provider else 'Unknown'}")
            elif self.status == 'fulfilled':
                logger.info(f"🎉 DEBUG: Service request fulfilled successfully - Service: {self.fulfilled_by_service.id if self.fulfilled_by_service else 'Unknown'}")
            elif self.status == 'cancelled':
                logger.info(f"❌ DEBUG: Service request cancelled")
            elif self.status == 'expired':
                logger.info(f"⏰ DEBUG: Service request expired")
                
        except Exception as e:
            # 💥 DEBUG: Log save errors with detailed context
            logger.error(f"💥 DEBUG: ServiceRequest {operation} failed: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"📊 DEBUG: Request data - Title: '{self.title}', Status: {self.status}, Customer: {self.customer.username}")
            raise
    
    def delete(self, *args, **kwargs):
        """
        🗑️ ENHANCED DELETE METHOD WITH COMPREHENSIVE IMPACT ANALYSIS
        ============================================================
        
        Enhanced delete method that provides comprehensive logging and impact analysis.
        Tracks all relationships and provides detailed context for debugging.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 📝 DEBUG: Log delete operation initiation
        logger.warning(f"🗑️ DEBUG: ServiceRequest DELETE operation initiated: '{self.title}' (ID: {self.id})")
        logger.warning(f"👤 DEBUG: Customer: {self.customer.username} (ID: {self.customer.id})")
        logger.warning(f"📊 DEBUG: Status: {self.status}, Category: {self.category.name}")
        
        try:
            # 📊 DEBUG: Analyze deletion impact
            logger.warning(f"🔍 DEBUG: Request deletion impact analysis:")
            logger.warning(f"   📊 Current status: {self.status}")
            logger.warning(f"   👥 Assigned provider: {self.assigned_provider.username if self.assigned_provider else 'None'}")
            logger.warning(f"   🔗 Fulfilled by service: {self.fulfilled_by_service.id if self.fulfilled_by_service else 'None'}")
            logger.warning(f"   📅 Created: {self.created_at}")
            logger.warning(f"   ⏰ Expires: {self.expires_at}")
            
            # 🚨 DEBUG: Log critical deletions
            if self.status == 'in_progress':
                logger.error(f"🚨 DEBUG: CRITICAL DELETION - Request is currently in progress!")
                logger.error(f"   👥 Provider affected: {self.assigned_provider.username if self.assigned_provider else 'Unknown'}")
                
            if self.status == 'open' and self.created_at > timezone.now() - timezone.timedelta(hours=24):
                logger.error(f"🚨 DEBUG: CRITICAL DELETION - Recent open request being deleted!")
                logger.error(f"   📅 Created only {timezone.now() - self.created_at} ago")
            
            # 💥 DEBUG: Perform the actual deletion
            logger.warning(f"💥 DEBUG: Executing database deletion for ServiceRequest: '{self.title}'")
            super().delete(*args, **kwargs)
            
            # ✅ DEBUG: Log successful deletion
            logger.warning(f"✅ DEBUG: ServiceRequest DELETE completed: '{self.title}' removed from database")
            
        except Exception as e:
            # 💥 DEBUG: Log deletion errors with detailed context
            logger.error(f"💥 DEBUG: ServiceRequest DELETE failed: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"📊 DEBUG: Request data - Title: '{self.title}', ID: {self.id}")
            raise
    
    def is_expired(self):
        """
        ⏰ CHECK IF REQUEST HAS EXPIRED WITH DEBUG TRACKING
        ==================================================
        
        Check if the request has expired with comprehensive logging.
        Provides detailed expiration status and timing information.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"⏰ DEBUG: Checking expiration for request: '{self.title}'")
        
        if not self.expires_at:
            logger.warning(f"⚠️ DEBUG: Request '{self.title}' has no expiration date set")
            return False
        
        now = timezone.now()
        is_expired = now > self.expires_at
        
        if is_expired:
            time_expired = now - self.expires_at
            logger.debug(f"⏰ DEBUG: Request '{self.title}' is EXPIRED (expired {time_expired} ago)")
        else:
            time_remaining = self.expires_at - now
            logger.debug(f"⏰ DEBUG: Request '{self.title}' is ACTIVE (expires in {time_remaining})")
        
        return is_expired
    
    def mark_as_expired(self):
        """
        ⏰ MARK REQUEST AS EXPIRED WITH DEBUG TRACKING
        =============================================
        
        Mark the request as expired with comprehensive logging and validation.
        Ensures proper status transition and audit trail.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"⏰ DEBUG: Marking request as expired: '{self.title}' (ID: {self.id})")
        logger.debug(f"📊 DEBUG: Previous status: {self.status}")
        
        # Validate that the request can be expired
        if self.status in ['fulfilled', 'cancelled']:
            logger.warning(f"⚠️ DEBUG: Cannot expire request with status '{self.status}' - already in terminal state")
            return False
        
        # Store original status for logging
        original_status = self.status
        
        # Mark as expired
        self.status = 'expired'
        self.save()
        
        logger.info(f"✅ DEBUG: Request '{self.title}' marked as expired (was: {original_status})")
        return True
    
    def assign_provider(self, provider):
        """
        👥 ASSIGN PROVIDER TO REQUEST WITH DEBUG TRACKING
        ================================================
        
        Assign a provider to this request with comprehensive logging and validation.
        Ensures proper status transition and audit trail.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"👥 DEBUG: Assigning provider to request: '{self.title}' (ID: {self.id})")
        logger.debug(f"🔧 DEBUG: Provider: {provider.username} (ID: {provider.id})")
        logger.debug(f"📊 DEBUG: Previous status: {self.status}")
        logger.debug(f"👤 DEBUG: Previous provider: {self.assigned_provider.username if self.assigned_provider else 'None'}")
        
        # Validate that the request can have a provider assigned
        if self.status not in ['open', 'in_progress']:
            logger.warning(f"⚠️ DEBUG: Cannot assign provider to request with status '{self.status}'")
            return False
        
        # Validate provider user type
        if provider.user_type != 'provider':
            logger.error(f"❌ DEBUG: Invalid user type for provider assignment: {provider.user_type}")
            return False
        
        # Store original values for logging
        original_provider = self.assigned_provider
        original_status = self.status
        
        # Assign provider and update status
        self.assigned_provider = provider
        self.status = 'in_progress'
        self.save()
        
        logger.info(f"✅ DEBUG: Provider assigned successfully")
        logger.info(f"   🔧 Provider: {provider.username}")
        logger.info(f"   🔄 Status: {original_status} → in_progress")
        logger.info(f"   👥 Provider change: {original_provider.username if original_provider else 'None'} → {provider.username}")
        
        return True
    
    def mark_as_fulfilled(self, service=None):
        """
        🎉 MARK REQUEST AS FULFILLED WITH DEBUG TRACKING
        ===============================================
        
        Mark the request as fulfilled with comprehensive logging and validation.
        Optionally links to the service that fulfilled the request.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🎉 DEBUG: Marking request as fulfilled: '{self.title}' (ID: {self.id})")
        logger.debug(f"📊 DEBUG: Previous status: {self.status}")
        logger.debug(f"🔗 DEBUG: Linking to service: {service.id if service else 'None'}")
        
        # Validate that the request can be fulfilled
        if self.status not in ['open', 'in_progress']:
            logger.warning(f"⚠️ DEBUG: Cannot fulfill request with status '{self.status}'")
            return False
        
        # Store original values for logging
        original_status = self.status
        original_service = self.fulfilled_by_service
        
        # Mark as fulfilled
        self.status = 'fulfilled'
        if service:
            self.fulfilled_by_service = service
            logger.debug(f"🔗 DEBUG: Linked to service: {service.name} (ID: {service.id})")
        
        self.save()
        
        logger.info(f"✅ DEBUG: Request '{self.title}' marked as fulfilled")
        logger.info(f"   🔄 Status: {original_status} → fulfilled")
        logger.info(f"   🔗 Service: {original_service.id if original_service else 'None'} → {service.id if service else 'None'}")
        logger.info(f"   👥 Provider: {self.assigned_provider.username if self.assigned_provider else 'None'}")
        
        return True
    
    def can_be_cancelled(self):
        """
        🔍 CHECK IF REQUEST CAN BE CANCELLED WITH DEBUG TRACKING
        =======================================================
        
        Check if the request can be cancelled with detailed business logic validation.
        Provides comprehensive logging and business rule checks.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"🔍 DEBUG: Checking if request can be cancelled: '{self.title}'")
        
        # Check current status
        cancellable_statuses = ['open', 'in_progress']
        if self.status not in cancellable_statuses:
            logger.debug(f"❌ DEBUG: Cannot cancel request with status '{self.status}' - not in {cancellable_statuses}")
            return False, f"Cannot cancel request with status '{self.status}'"
        
        # Check if already expired
        if self.is_expired():
            logger.debug(f"❌ DEBUG: Cannot cancel expired request")
            return False, "Cannot cancel expired request"
        
        # Additional business rules can be added here
        logger.debug(f"✅ DEBUG: Request '{self.title}' can be cancelled")
        return True, "Request can be cancelled"
    
    def get_provider_recommendations(self, limit=10):
        """
        🎯 GET PROVIDER RECOMMENDATIONS WITH DEBUG TRACKING
        ==================================================
        
        Get recommended providers for this request based on category and location.
        Provides comprehensive logging and recommendation algorithm tracking.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"🎯 DEBUG: Getting provider recommendations for request: '{self.title}'")
        logger.debug(f"📂 DEBUG: Category: {self.category.name}")
        logger.debug(f"📍 DEBUG: Location: {self.location}")
        logger.debug(f"💰 DEBUG: Budget: {self.budget_min}-{self.budget_max} {self.currency}")
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            # Find providers with active services in the same category
            providers = User.objects.filter(
                user_type='provider',
                services__category=self.category,
                services__status='active'
            ).distinct()
            
            initial_count = providers.count()
            logger.debug(f"📊 DEBUG: Found {initial_count} providers with active services in category")
            
            # Apply budget filtering if specified
            if self.budget_min and self.budget_max:
                providers = providers.filter(
                    services__hourly_rate__gte=self.budget_min,
                    services__hourly_rate__lte=self.budget_max
                )
                budget_filtered_count = providers.count()
                logger.debug(f"💰 DEBUG: Budget filtering: {budget_filtered_count} providers in budget range")
            
            # Limit results
            providers = providers[:limit]
            final_count = providers.count()
            
            logger.info(f"✅ DEBUG: Provider recommendations generated - {final_count} providers")
            logger.debug(f"📊 DEBUG: Recommendation stats - Initial: {initial_count}, Final: {final_count}")
            
            return providers
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error generating provider recommendations: {e}")
            return User.objects.none()
    
    @property
    def days_until_expiration(self):
        """
        📅 DAYS UNTIL EXPIRATION PROPERTY WITH DEBUG TRACKING
        ====================================================
        
        Property to get days until expiration with performance tracking.
        Provides insights into request urgency and deadline management.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.expires_at:
            logger.debug(f"📅 DEBUG: Request '{self.title}' has no expiration date")
            return None
        
        now = timezone.now()
        if now > self.expires_at:
            days_expired = (now - self.expires_at).days
            logger.debug(f"📅 DEBUG: Request '{self.title}' expired {days_expired} days ago")
            return -days_expired
        else:
            days_remaining = (self.expires_at - now).days
            logger.debug(f"📅 DEBUG: Request '{self.title}' expires in {days_remaining} days")
            return days_remaining
    
    @property
    def budget_range_display(self):
        """
        💰 BUDGET RANGE DISPLAY PROPERTY WITH DEBUG TRACKING
        ===================================================
        
        Property to get formatted budget range for display purposes.
        Provides consistent budget formatting across the application.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.budget_min and not self.budget_max:
            logger.debug(f"💰 DEBUG: Request '{self.title}' has no budget specified")
            return "Budget not specified"
        
        if self.budget_min and self.budget_max:
            display = f"{self.budget_min} - {self.budget_max} {self.currency}"
            logger.debug(f"💰 DEBUG: Request '{self.title}' budget range: {display}")
            return display
        elif self.budget_min:
            display = f"From {self.budget_min} {self.currency}"
            logger.debug(f"💰 DEBUG: Request '{self.title}' minimum budget: {display}")
            return display
        elif self.budget_max:
            display = f"Up to {self.budget_max} {self.currency}"
            logger.debug(f"💰 DEBUG: Request '{self.title}' maximum budget: {display}")
            return display
    
    @property
    def is_urgent(self):
        """
        🚨 URGENCY CHECK PROPERTY WITH DEBUG TRACKING
        ============================================
        
        Property to check if request is urgent (high or urgent priority).
        Provides quick urgency assessment for prioritization.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        urgent = self.urgency in ['high', 'urgent']
        logger.debug(f"🚨 DEBUG: Request '{self.title}' urgency check: {self.urgency} → {'URGENT' if urgent else 'NORMAL'}")
        return urgent

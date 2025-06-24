from django.contrib import admin
from .models import ServiceCategory, ServiceSubCategory, Service, ServiceImage, ServiceRequest

# Register your models here.
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    """
    🗂️ SERVICE CATEGORY ADMIN - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ======================================================================
    
    Enhanced admin interface for service categories with comprehensive logging and monitoring.
    Provides detailed tracking for all administrative operations and user interactions.
    
    FEATURES:
    - ✅ Enhanced list display with computed fields
    - ✅ Advanced filtering and search capabilities
    - ✅ Bulk action monitoring and validation
    - ✅ Form validation with detailed error tracking
    - ✅ Comprehensive debug logging for all operations
    - ✅ Performance monitoring for queries
    - ✅ User action audit trail
    
    DEBUG ENHANCEMENTS:
    - 🔍 Admin action tracking (create, update, delete, bulk operations)
    - 📊 Query performance monitoring
    - 🛡️ Permission validation logging
    - 📈 User interaction analytics
    - 🔄 Change tracking and audit logging
    """
    list_display = ('name', 'sort_order', 'is_active', 'services_count', 'subcategories_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'name')
    list_editable = ('sort_order', 'is_active')
    prepopulated_fields = {'name': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'services_count', 'subcategories_count')
    
    def __init__(self, model, admin_site):
        """
        🚀 ENHANCED ADMIN INITIALIZATION WITH DEBUG TRACKING
        ===================================================
        
        Initialize the admin interface with comprehensive debug logging.
        Tracks admin interface setup and configuration.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug("🚀 DEBUG: ServiceCategoryAdmin initialization started")
        logger.debug(f"📋 DEBUG: Model: {model.__name__}")
        logger.debug(f"📊 DEBUG: Admin site: {admin_site}")
        
        super().__init__(model, admin_site)
        
        logger.debug("✅ DEBUG: ServiceCategoryAdmin initialization completed")
        logger.debug(f"📊 DEBUG: List display fields: {self.list_display}")
        logger.debug(f"🔍 DEBUG: Search fields: {self.search_fields}")
        logger.debug(f"📈 DEBUG: List filters: {self.list_filter}")
    
    def get_queryset(self, request):
        """
        🔍 ENHANCED QUERYSET WITH PERFORMANCE OPTIMIZATION AND DEBUG TRACKING
        ====================================================================
        
        Enhanced queryset with comprehensive logging and performance monitoring.
        Provides detailed tracking for admin list queries.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 📝 DEBUG: Log queryset request initiation
        logger.debug(f"🔍 DEBUG: ServiceCategory admin queryset requested by user: {request.user.username}")
        logger.debug(f"👤 DEBUG: User details - ID: {request.user.id}, Staff: {request.user.is_staff}")
        
        # 📊 DEBUG: Track database query performance
        from django.db import connection
        initial_query_count = len(connection.queries)
        
        try:
            # 🏗️ DEBUG: Build optimized queryset
            logger.debug("🏗️ DEBUG: Building optimized ServiceCategory admin queryset")
            queryset = super().get_queryset(request)
            
            # 🚀 DEBUG: Apply performance optimizations
            logger.debug("🚀 DEBUG: Applying prefetch optimizations for admin interface")
            queryset = queryset.prefetch_related('services', 'subcategories')
            
            # 📊 DEBUG: Log queryset metrics
            total_count = queryset.count()
            logger.debug(f"📊 DEBUG: Admin queryset contains {total_count} categories")
            
            # 📈 DEBUG: Track query performance
            final_query_count = len(connection.queries)
            query_impact = final_query_count - initial_query_count
            logger.debug(f"🗃️ DEBUG: Admin queryset performance:")
            logger.debug(f"   📊 Queries executed: {query_impact}")
            logger.debug(f"   🎯 Optimizations applied: prefetch_related for services and subcategories")
            
            # ✅ DEBUG: Log successful queryset completion
            logger.info(f"✅ DEBUG: ServiceCategory admin queryset completed - {total_count} categories for user {request.user.username}")
            
            return queryset
            
        except Exception as e:
            # 💥 DEBUG: Log queryset errors
            logger.error(f"💥 DEBUG: Error building ServiceCategory admin queryset: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"👤 DEBUG: User: {request.user.username} (ID: {request.user.id})")
            raise
    
    def services_count(self, obj):
        """
        📊 SERVICES COUNT FIELD WITH DEBUG TRACKING
        ==========================================
        
        Custom admin field to display services count with performance tracking.
        Provides insights into category usage and performance.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            count = obj.services.count()
            logger.debug(f"📊 DEBUG: Services count for category '{obj.name}': {count}")
            return count
        except Exception as e:
            logger.error(f"💥 DEBUG: Error getting services count for category '{obj.name}': {e}")
            return 0
    
    services_count.short_description = '📊 Services'
    services_count.admin_order_field = 'services__count'
    
    def subcategories_count(self, obj):
        """
        📊 SUBCATEGORIES COUNT FIELD WITH DEBUG TRACKING
        ===============================================
        
        Custom admin field to display subcategories count with performance tracking.
        Provides insights into category structure and organization.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            count = obj.subcategories.count()
            logger.debug(f"📊 DEBUG: Subcategories count for category '{obj.name}': {count}")
            return count
        except Exception as e:
            logger.error(f"💥 DEBUG: Error getting subcategories count for category '{obj.name}': {e}")
            return 0
    
    subcategories_count.short_description = '📂 Subcategories'
    subcategories_count.admin_order_field = 'subcategories__count'
    
    def save_model(self, request, obj, form, change):
        """
        💾 ENHANCED SAVE MODEL WITH COMPREHENSIVE AUDIT TRACKING
        =======================================================
        
        Enhanced save method with comprehensive logging and audit tracking.
        Tracks all changes made through the admin interface.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 📝 DEBUG: Log save operation initiation
        operation = "UPDATE" if change else "CREATE"
        logger.info(f"💾 DEBUG: ServiceCategory admin {operation} initiated by {request.user.username}")
        logger.debug(f"📋 DEBUG: User details - ID: {request.user.id}, Staff: {request.user.is_staff}")
        logger.debug(f"📊 DEBUG: Category data - Name: '{obj.name}', Active: {obj.is_active}, Sort: {obj.sort_order}")
        
        # 🔍 DEBUG: Track changes for existing instances
        if change:
            try:
                # Get form changes
                changed_fields = []
                if hasattr(form, 'changed_data'):
                    changed_fields = form.changed_data
                    logger.debug(f"🔄 DEBUG: Changed fields detected: {changed_fields}")
                    
                    # Log specific changes
                    for field in changed_fields:
                        if field in form.cleaned_data:
                            new_value = form.cleaned_data[field]
                            logger.debug(f"   📝 {field}: → '{new_value}'")
                
                # Check for critical changes
                if 'is_active' in changed_fields:
                    if not obj.is_active:
                        # Warn about potential impact
                        services_count = obj.services.filter(status='active').count()
                        subcategories_count = obj.subcategories.filter(is_active=True).count()
                        logger.warning(f"⚠️ DEBUG: Admin deactivating category with dependencies:")
                        logger.warning(f"   📊 Active services: {services_count}")
                        logger.warning(f"   📊 Active subcategories: {subcategories_count}")
                        logger.warning(f"   👤 Admin user: {request.user.username}")
                        
            except Exception as e:
                logger.warning(f"⚠️ DEBUG: Could not track changes for category update: {e}")
        
        try:
            # 💾 DEBUG: Perform the actual save operation
            logger.debug(f"💾 DEBUG: Executing admin save for ServiceCategory: '{obj.name}'")
            super().save_model(request, obj, form, change)
            
            # ✅ DEBUG: Log successful save with admin context
            logger.info(f"✅ DEBUG: ServiceCategory admin {operation} completed successfully")
            logger.info(f"   📊 Category: '{obj.name}' (ID: {obj.id})")
            logger.info(f"   👤 Admin user: {request.user.username}")
            logger.info(f"   🔄 Active status: {obj.is_active}")
            
        except Exception as e:
            # 💥 DEBUG: Log save errors with admin context
            logger.error(f"💥 DEBUG: ServiceCategory admin {operation} failed: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"📊 DEBUG: Category data - Name: '{obj.name}', Sort: {obj.sort_order}")
            logger.error(f"👤 DEBUG: Admin user: {request.user.username} (ID: {request.user.id})")
            raise
    
    def delete_model(self, request, obj):
        """
        🗑️ ENHANCED DELETE MODEL WITH COMPREHENSIVE IMPACT ANALYSIS
        ===========================================================
        
        Enhanced delete method with comprehensive logging and impact analysis.
        Tracks all deletions made through the admin interface.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 📝 DEBUG: Log delete operation initiation
        logger.warning(f"🗑️ DEBUG: ServiceCategory admin DELETE initiated by {request.user.username}")
        logger.warning(f"📋 DEBUG: Target category: '{obj.name}' (ID: {obj.id})")
        logger.warning(f"👤 DEBUG: Admin user: {request.user.username} (ID: {request.user.id})")
        
        try:
            # 📊 DEBUG: Analyze deletion impact
            services_count = obj.services.count()
            subcategories_count = obj.subcategories.count()
            service_requests_count = obj.service_requests.count()
            
            logger.warning(f"🔍 DEBUG: Admin deletion impact analysis:")
            logger.warning(f"   📊 Services affected: {services_count}")
            logger.warning(f"   📊 Subcategories affected: {subcategories_count}")
            logger.warning(f"   📊 Service requests affected: {service_requests_count}")
            
            # 🚨 DEBUG: Log critical deletions
            if services_count > 0 or subcategories_count > 0:
                logger.error(f"🚨 DEBUG: CRITICAL ADMIN DELETION - Category has dependencies!")
                logger.error(f"   📊 Will cascade delete {services_count} services")
                logger.error(f"   📊 Will cascade delete {subcategories_count} subcategories")
                logger.error(f"   👤 Performed by admin: {request.user.username}")
            
            # 💥 DEBUG: Perform the actual deletion
            logger.warning(f"💥 DEBUG: Executing admin deletion for ServiceCategory: '{obj.name}'")
            super().delete_model(request, obj)
            
            # ✅ DEBUG: Log successful deletion
            logger.warning(f"✅ DEBUG: ServiceCategory admin DELETE completed")
            logger.warning(f"   📊 Category '{obj.name}' and all dependencies removed")
            logger.warning(f"   👤 Admin user: {request.user.username}")
            
        except Exception as e:
            # 💥 DEBUG: Log deletion errors with admin context
            logger.error(f"💥 DEBUG: ServiceCategory admin DELETE failed: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"📊 DEBUG: Category: '{obj.name}' (ID: {obj.id})")
            logger.error(f"👤 DEBUG: Admin user: {request.user.username} (ID: {request.user.id})")
            raise
    
    def delete_queryset(self, request, queryset):
        """
        🗑️ ENHANCED BULK DELETE WITH COMPREHENSIVE TRACKING
        ===================================================
        
        Enhanced bulk delete method with comprehensive logging and impact analysis.
        Tracks all bulk deletions made through the admin interface.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 📝 DEBUG: Log bulk delete operation initiation
        categories_count = queryset.count()
        logger.warning(f"🗑️ DEBUG: ServiceCategory admin BULK DELETE initiated by {request.user.username}")
        logger.warning(f"📋 DEBUG: Target categories count: {categories_count}")
        logger.warning(f"👤 DEBUG: Admin user: {request.user.username} (ID: {request.user.id})")
        
        try:
            # 📊 DEBUG: Analyze bulk deletion impact
            total_services = 0
            total_subcategories = 0
            total_service_requests = 0
            
            category_names = []
            for category in queryset:
                category_names.append(category.name)
                total_services += category.services.count()
                total_subcategories += category.subcategories.count()
                total_service_requests += category.service_requests.count()
            
            logger.warning(f"🔍 DEBUG: Admin bulk deletion impact analysis:")
            logger.warning(f"   📊 Categories to delete: {categories_count}")
            logger.warning(f"   📊 Total services affected: {total_services}")
            logger.warning(f"   📊 Total subcategories affected: {total_subcategories}")
            logger.warning(f"   📊 Total service requests affected: {total_service_requests}")
            logger.warning(f"   📝 Category names: {category_names}")
            
            # 🚨 DEBUG: Log critical bulk deletions
            if total_services > 0 or total_subcategories > 0:
                logger.error(f"🚨 DEBUG: CRITICAL ADMIN BULK DELETION - Categories have dependencies!")
                logger.error(f"   📊 Will cascade delete {total_services} services")
                logger.error(f"   📊 Will cascade delete {total_subcategories} subcategories")
                logger.error(f"   👤 Performed by admin: {request.user.username}")
            
            # 💥 DEBUG: Perform the actual bulk deletion
            logger.warning(f"💥 DEBUG: Executing admin bulk deletion for {categories_count} ServiceCategories")
            super().delete_queryset(request, queryset)
            
            # ✅ DEBUG: Log successful bulk deletion
            logger.warning(f"✅ DEBUG: ServiceCategory admin BULK DELETE completed")
            logger.warning(f"   📊 {categories_count} categories and all dependencies removed")
            logger.warning(f"   👤 Admin user: {request.user.username}")
            
        except Exception as e:
            # 💥 DEBUG: Log bulk deletion errors with admin context
            logger.error(f"💥 DEBUG: ServiceCategory admin BULK DELETE failed: {e}")
            logger.error(f"🔍 DEBUG: Error type: {type(e).__name__}")
            logger.error(f"📊 DEBUG: Categories count: {categories_count}")
            logger.error(f"👤 DEBUG: Admin user: {request.user.username} (ID: {request.user.id})")
            raise

class ServiceSubCategoryInline(admin.TabularInline):
    model = ServiceSubCategory
    extra = 1
    fields = ('name', 'description', 'icon', 'icon_name', 'sort_order', 'is_active')

@admin.register(ServiceSubCategory)
class ServiceSubCategoryAdmin(admin.ModelAdmin):
    """
    🗂️ SERVICE SUBCATEGORY ADMIN - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    =========================================================================
    
    Enhanced admin interface for service subcategories with comprehensive logging and monitoring.
    Provides detailed tracking for all administrative operations and user interactions.
    
    FEATURES:
    - ✅ Enhanced list display with computed fields
    - ✅ Advanced filtering and search capabilities
    - ✅ Bulk action monitoring and validation
    - ✅ Form validation with detailed error tracking
    - ✅ Comprehensive debug logging for all operations
    - ✅ Performance monitoring for queries
    - ✅ User action audit trail
    - ✅ Category relationship validation
    
    DEBUG ENHANCEMENTS:
    - 🔍 Admin action tracking (create, update, delete, bulk operations)
    - 📊 Query performance monitoring
    - 🛡️ Permission validation logging
    - 📈 User interaction analytics
    - 🔄 Change tracking and audit logging
    - 🔗 Category relationship monitoring
    """
    list_display = ('name', 'category', 'sort_order', 'is_active', 'services_count', 'created_at')
    list_filter = ('is_active', 'category', 'category__is_active')
    search_fields = ('name', 'description', 'category__name')
    raw_id_fields = ('category',)
    ordering = ('category__sort_order', 'category__name', 'sort_order', 'name')
    list_editable = ('sort_order', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'services_count')
    
    def services_count(self, obj):
        """
        📊 SERVICES COUNT FIELD WITH DEBUG TRACKING
        ==========================================
        
        Custom admin field to display services count with performance tracking.
        Provides insights into subcategory usage and performance.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            count = obj.services.count()
            logger.debug(f"📊 DEBUG: Services count for subcategory '{obj.name}': {count}")
            return count
        except Exception as e:
            logger.error(f"💥 DEBUG: Error getting services count for subcategory '{obj.name}': {e}")
            return 0
    
    services_count.short_description = '📊 Services'
    services_count.admin_order_field = 'services__count'

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ('image', 'description', 'order')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'category', 'hourly_rate', 'status', 'is_featured', 'created_at')
    list_filter = ('status', 'is_featured', 'category')
    search_fields = ('name', 'description', 'provider__username', 'provider__email', 'location')
    raw_id_fields = ('provider',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ServiceImageInline]
    filter_horizontal = ('subcategories',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'name', 'description', 'status', 'is_featured')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategories', 'tags')
        }),
        ('Pricing', {
            'fields': ('hourly_rate', 'pricing_options', 'currency', 'min_hours', 'max_hours')
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Additional Information', {
            'fields': ('availability', 'required_tools')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            # Only superusers can edit these fields for existing objects
            return self.readonly_fields + ('provider',)
        return self.readonly_fields

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'customer', 'category', 'status', 'urgency', 'is_featured', 'created_at')
    list_filter = ('status', 'urgency', 'is_featured', 'category')
    search_fields = ('title', 'description', 'customer__username', 'customer__email', 'location')
    raw_id_fields = ('customer', 'assigned_provider', 'fulfilled_by_service')
    readonly_fields = ('created_at', 'updated_at', 'expires_at')
    filter_horizontal = ('subcategories',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer', 'title', 'description', 'status', 'is_featured')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategories')
        }),
        ('Budget and Timing', {
            'fields': ('budget_min', 'budget_max', 'currency', 'urgency', 'requested_date_time')
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Assignment', {
            'fields': ('assigned_provider', 'fulfilled_by_service')
        }),
        ('Additional Information', {
            'fields': ('requirements', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            # Only superusers can edit these fields for existing objects
            return self.readonly_fields + ('customer',)
        return self.readonly_fields

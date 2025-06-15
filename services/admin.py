from django.contrib import admin
from .models import ServiceCategory, ServiceSubCategory, Service, ServiceImage, ServiceRequest

# Register your models here.
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'sort_order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'name')
    list_editable = ('sort_order', 'is_active')
    prepopulated_fields = {'name': ('name',)}

class ServiceSubCategoryInline(admin.TabularInline):
    model = ServiceSubCategory
    extra = 1
    fields = ('name', 'description', 'icon', 'icon_url', 'sort_order', 'is_active')

@admin.register(ServiceSubCategory)
class ServiceSubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'sort_order', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'description', 'category__name')
    raw_id_fields = ('category',)
    ordering = ('category__sort_order', 'category__name', 'sort_order', 'name')
    list_editable = ('sort_order', 'is_active')

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

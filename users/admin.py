from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, AccessToken, Pass

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_staff')
    list_filter = ('user_type', 'is_verified', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('username', 'email')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture', 'bio', 'location')}),
        (_('Account info'), {'fields': ('user_type', 'is_verified', 'rating', 'balance')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type'),
        }),
    )

# Register the User model with the custom admin class
admin.site.register(User, UserAdmin)


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'device_name', 'created_at', 'last_refreshed_at', 'is_active')
    list_filter = ('device_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'token_jti', 'device_name', 'ip_address')
    readonly_fields = ('id', 'created_at', 'last_used_at', 'last_refreshed_at')
    date_hierarchy = 'created_at'
    

@admin.register(Pass)
class PassAdmin(admin.ModelAdmin):
    list_display = ('user_passing', 'user_passed', 'timestamp')
    search_fields = ('user_passing__username', 'user_passed__username')
    date_hierarchy = 'timestamp'

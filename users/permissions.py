from rest_framework import permissions

class IsCustomer(permissions.BasePermission):
    """
    Permission to only allow customers to access the view
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'customer'

class IsServiceProvider(permissions.BasePermission):
    """
    Permission to only allow service providers to access the view
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'provider'

class IsAdmin(permissions.BasePermission):
    """
    Permission to only allow administrators to access the view
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'admin'

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

class IsVerificationOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a verification to view or edit it.
    """
    message = "You must be the owner of this verification to perform this action."

    def has_object_permission(self, request, view, obj):
        # Check if user is the owner of the verification
        return obj.user == request.user

class IsVerificationAdmin(permissions.BasePermission):
    """
    Custom permission to only allow administrators to update verification status.
    """
    message = "Only administrators can update verification status."

    def has_permission(self, request, view):
        # Check if user is authenticated first
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Check if user is staff or has admin role or has explicit verification admin permission
        return (request.user.is_staff or 
                getattr(request.user, 'is_admin', False) or
                request.user.has_perm('verification.change_verification_status'))

    def has_object_permission(self, request, view, obj):
        # Recheck permission at object level
        return self.has_permission(request, view)

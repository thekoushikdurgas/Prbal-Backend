from rest_framework import permissions

class IsServiceProvider(permissions.BasePermission):
    """
    Custom permission to only allow service providers to perform certain actions.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'PROVIDER'
        )

    def has_object_permission(self, request, view, obj):
        # Allow read permissions to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.provider == request.user

class IsCustomer(permissions.BasePermission):
    """
    Custom permission to only allow customers to perform certain actions.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'CUSTOMER'
        )

    def has_object_permission(self, request, view, obj):
        # Allow read permissions to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.customer == request.user
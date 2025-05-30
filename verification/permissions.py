from rest_framework import permissions

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
        # Check if user is staff or has admin role
        return request.user.is_staff or getattr(request.user, 'is_admin', False)

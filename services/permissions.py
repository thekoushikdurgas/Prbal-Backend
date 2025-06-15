from rest_framework import permissions

class IsServiceProvider(permissions.BasePermission):
    """
    Custom permission to only allow service providers to create services.
    """
    message = "Only service providers can create or modify services."

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to service providers
        return request.user.is_authenticated and request.user.user_type == 'provider'

class IsCustomer(permissions.BasePermission):
    """
    Custom permission to only allow customers to create service requests.
    """
    message = "Only customers can create or modify service requests."

    def has_permission(self, request, view):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to customers
        return request.user.is_authenticated and request.user.user_type == 'customer'

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit or delete it.
    """
    message = "You must be the owner of this object to perform this action."

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request, so we'll always allow GET, HEAD or OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the owner of the object
        if hasattr(obj, 'provider'):
            return obj.provider == request.user
        elif hasattr(obj, 'seller'):
            return obj.seller == request.user
        
        return False

from rest_framework import permissions

class IsProvider(permissions.BasePermission):
    """
    Custom permission to only allow service providers to create bids.
    """
    message = "Only service providers can create bids."

    def has_permission(self, request, view):
        # Write permissions are only allowed to service providers
        return request.user.is_authenticated and request.user.user_type == 'provider'

class IsBidOwner(permissions.BasePermission):
    """
    Custom permission to only allow the owner of a bid (provider) to update it.
    """
    message = "You must be the owner of this bid to perform this action."

    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the bid owner
        return obj.provider == request.user

class IsBidParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants (provider or customer) to view bid details.
    """
    message = "You must be a participant in this bid to perform this action."

    def has_object_permission(self, request, view, obj):
        # Check if user is the provider or the customer of the service
        is_provider = obj.provider == request.user
        is_customer = obj.service.provider == request.user  # The customer is interested in the provider's service
        
        return is_provider or is_customer

class IsBidCustomer(permissions.BasePermission):
    """
    Custom permission to only allow the customer to accept or reject bids.
    """
    message = "Only the customer can accept or reject bids."

    def has_object_permission(self, request, view, obj):
        # Only the customer can accept or reject bids
        # In this case, the customer is interested in the provider's service
        return obj.service.provider == request.user

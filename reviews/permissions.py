from rest_framework import permissions

class IsReviewOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a review to edit it.
    """
    message = "You must be the owner of this review to perform this action."

    def has_object_permission(self, request, view, obj):
        # Check if user is the client (reviewer)
        return obj.client == request.user

class IsReviewProvider(permissions.BasePermission):
    """
    Custom permission to only allow the provider to respond to a review.
    """
    message = "You must be the provider of this service to respond to the review."

    def has_object_permission(self, request, view, obj):
        # Check if user is the provider
        return obj.provider == request.user

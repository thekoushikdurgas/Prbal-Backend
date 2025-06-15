from rest_framework import permissions

class IsNotificationRecipient(permissions.BasePermission):
    """
    Custom permission to only allow the recipient of a notification to view or modify it.
    """
    message = "You must be the recipient of this notification to perform this action."

    def has_object_permission(self, request, view, obj):
        # Check if user is the recipient of the notification
        return obj.recipient == request.user

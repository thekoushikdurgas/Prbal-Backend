from rest_framework import permissions

class IsThreadParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants of a message thread to view or interact with it.
    """
    message = "You must be a participant in this thread to perform this action."

    def has_object_permission(self, request, view, obj):
        # Check if user is a participant in the thread
        return request.user in obj.participants.all()

class IsMessageSender(permissions.BasePermission):
    """
    Custom permission to only allow the sender of a message to update or delete it.
    """
    message = "You must be the sender of this message to perform this action."

    def has_object_permission(self, request, view, obj):
        # Check if user is the sender of the message
        return obj.sender == request.user

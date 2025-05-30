from rest_framework import permissions

class IsSuggestionOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a suggestion to view or provide feedback on it.
    """
    message = "You must be the recipient of this suggestion to perform this action."

    def has_object_permission(self, request, view, obj):
        # Check if user is the owner of the suggestion
        return obj.user == request.user

class CanLogAIFeedback(permissions.BasePermission):
    """
    Custom permission to allow users to log feedback for AI suggestions they've interacted with.
    """
    message = "You can only log feedback for suggestions or bids you've interacted with."

    def has_permission(self, request, view):
        # Everyone with authentication can log feedback
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # For suggestion feedback, check if user is the suggestion recipient
        if hasattr(obj, 'suggestion') and obj.suggestion:
            return obj.suggestion.user == request.user
        
        # For bid feedback, check if user is the bid creator or recipient
        if hasattr(obj, 'bid') and obj.bid:
            return obj.bid.provider == request.user or obj.bid.service.provider == request.user
        
        return False

from rest_framework import permissions

class IsBookingParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants (provider or customer) in a booking 
    to view, update or manage the booking.
    """
    message = "You must be a participant in this booking to perform this action."

    def has_object_permission(self, request, view, obj):
        # Check if user is the provider or the customer of the booking
        return obj.provider == request.user or obj.customer == request.user

class CanChangeBookingStatus(permissions.BasePermission):
    """
    Custom permission to control who can change booking status and to which status.
    Different status transitions have different permissions.
    """
    message = "You don't have permission to change the booking status in this way."

    def has_object_permission(self, request, view, obj):
        # Base permission - must be a participant
        if not (obj.provider == request.user or obj.customer == request.user):
            return False
            
        # Get the new status from the request data
        new_status = request.data.get('status')
        if not new_status:
            return True  # Not changing status
            
        # Define allowed transitions based on role and current status
        # Provider transitions
        if request.user == obj.provider:
            if obj.status == 'confirmed' and new_status == 'in_progress':
                return True
            if obj.status == 'in_progress' and new_status == 'completed':
                return True
            if obj.status in ['pending', 'confirmed', 'in_progress'] and new_status == 'disputed':
                return True
                
        # Customer transitions
        if request.user == obj.customer:
            if obj.status == 'pending' and new_status == 'confirmed':
                return True
            if obj.status in ['pending', 'confirmed', 'in_progress'] and new_status == 'cancelled':
                return True
            if obj.status in ['pending', 'confirmed', 'in_progress'] and new_status == 'disputed':
                return True
                
        # Admin can make any transition (would need additional check for admin)
        if request.user.is_staff:
            return True
            
        return False

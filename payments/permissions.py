from rest_framework import permissions

class IsPaymentParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants (payer or payee) to view a payment.
    """
    message = "You must be a participant in this payment to perform this action."

    def has_object_permission(self, request, view, obj):
        # Check if user is the payer or payee of the payment
        return obj.payer == request.user or obj.payee == request.user

class IsPaymentPayer(permissions.BasePermission):
    """
    Custom permission to only allow the payer to initiate or confirm a payment.
    """
    message = "Only the payer can initiate or confirm a payment."

    def has_object_permission(self, request, view, obj):
        # Check if user is the payer of the payment
        return obj.payer == request.user

class IsPayoutProvider(permissions.BasePermission):
    """
    Custom permission to only allow the provider to view or request their own payouts.
    """
    message = "You can only view or request your own payouts."

    def has_object_permission(self, request, view, obj):
        # Check if user is the provider for this payout
        return obj.provider == request.user

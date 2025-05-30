from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from .models import Verification
from .serializers import (
    VerificationListSerializer,
    VerificationDetailSerializer,
    VerificationCreateSerializer,
    VerificationUpdateSerializer,
    VerificationAdminUpdateSerializer
)
from .permissions import IsVerificationOwner, IsVerificationAdmin

class VerificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for verification requests - allows listing, retrieving, creating, and updating.
    Normal users can only view and submit their own verification requests.
    Admins can update status and provide verification notes.
    """
    queryset = Verification.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['verification_type', 'document_type', 'status']
    ordering_fields = ['created_at', 'updated_at', 'verified_at']
    ordering = ['-created_at']  # Most recent first by default
    
    def get_queryset(self):
        user = self.request.user
        
        # If user is not authenticated, return nothing
        if not user.is_authenticated:
            return Verification.objects.none()
            
        # Admins can see all verifications
        if user.is_staff:
            return Verification.objects.all()
            
        # Normal users see only their own verifications
        return Verification.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VerificationDetailSerializer
        elif self.action == 'create':
            return VerificationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            # Use admin serializer for staff users
            if self.request.user.is_staff:
                return VerificationAdminUpdateSerializer
            return VerificationUpdateSerializer
        return VerificationListSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only admins can update verification status
            if self.request.user.is_staff:
                return [permissions.IsAuthenticated(), IsVerificationAdmin()]
            # Users can only update their own verifications
            return [permissions.IsAuthenticated(), IsVerificationOwner()]
        elif self.action == 'retrieve':
            # Both owners and admins can view verification details
            return [permissions.IsAuthenticated(), IsVerificationOwner() | IsVerificationAdmin()]
        # List is filtered by user in get_queryset
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        # Set the user to the current user
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a pending verification request.
        Only the owner can cancel their own verification, and only if it's in pending status.
        """
        verification = self.get_object()
        
        if verification.status != 'pending':
            return Response({
                'detail': "Only pending verification requests can be cancelled."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete the verification request
        verification.delete()
        
        return Response({
            'status': 'success',
            'message': "Verification request cancelled successfully."
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsVerificationAdmin])
    def mark_verified(self, request, pk=None):
        """
        Mark a verification as verified.
        Only admins can use this endpoint.
        """
        verification = self.get_object()
        notes = request.data.get('notes', '')
        
        verification.mark_as_verified(verified_by=request.user, notes=notes)
        
        return Response({
            'status': 'success',
            'message': "Verification marked as verified successfully."
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsVerificationAdmin])
    def mark_rejected(self, request, pk=None):
        """
        Mark a verification as rejected with a reason.
        Only admins can use this endpoint.
        """
        verification = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response({
                'detail': "Rejection reason is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        verification.mark_as_rejected(reason=reason, verified_by=request.user)
        
        return Response({
            'status': 'success',
            'message': "Verification marked as rejected successfully."
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def status_summary(self, request):
        """
        Get summary of verification status for the current user.
        Returns counts of verifications by type and status.
        """
        user = request.user
        
        # Get all verifications for the user
        verifications = Verification.objects.filter(user=user)
        
        # Get all types and their verification status
        verification_types = dict(Verification.VERIFICATION_TYPE_CHOICES)
        
        # Initialize summary
        summary = {}
        for v_type, v_label in verification_types.items():
            # Get the latest verification of each type
            latest = verifications.filter(verification_type=v_type).order_by('-created_at').first()
            
            if latest:
                summary[v_type] = {
                    'label': v_label,
                    'status': latest.status,
                    'status_display': latest.get_status_display(),
                    'verified': latest.status == 'verified',
                    'expired': latest.is_expired() if latest.status == 'verified' else False,
                    'last_updated': latest.updated_at,
                    'verification_id': latest.id
                }
            else:
                summary[v_type] = {
                    'label': v_label,
                    'status': 'not_submitted',
                    'status_display': 'Not Submitted',
                    'verified': False,
                    'expired': False,
                    'last_updated': None,
                    'verification_id': None
                }
        
        return Response(summary, status=status.HTTP_200_OK)

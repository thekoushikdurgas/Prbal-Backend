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
    ViewSet for verification requests.
    Allows listing, retrieving, creating, and updating verification requests.
    Normal users can only view and submit their own verification requests.
    Admins can update status and provide verification notes.
    """
    queryset = Verification.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['verification_type', 'document_type', 'status']
    ordering_fields = ['created_at', 'updated_at', 'verified_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Verification.objects.none()
        if user.is_staff:
            return Verification.objects.all()
        return Verification.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VerificationDetailSerializer
        elif self.action == 'create':
            return VerificationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            if self.request.user.is_staff:
                return VerificationAdminUpdateSerializer
            return VerificationUpdateSerializer
        return VerificationListSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'mark_verified', 'mark_rejected', 'mark_in_progress']:
            # Only admins can update verification status
            return [permissions.IsAuthenticated(), IsVerificationAdmin()]
        elif self.action == 'retrieve':
            # Both owners and admins can view verification details
            return [permissions.IsAuthenticated(), IsVerificationOwner() | IsVerificationAdmin()]
        elif self.action == 'cancel':
            # Only owners can cancel their verifications
            return [permissions.IsAuthenticated(), IsVerificationOwner()]
        # List is filtered by user in get_queryset
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending verification request"""
        verification = self.get_object()
        try:
            verification.cancel(cancelled_by=request.user)
            return Response({
                'status': 'success',
                'message': 'Verification request cancelled successfully.'
            })
        except ValueError as e:
            return Response({
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_in_progress(self, request, pk=None):
        """Mark a verification as in progress"""
        verification = self.get_object()
        notes = request.data.get('verification_notes', '')
        try:
            verification.mark_as_in_progress(notes=notes, admin=request.user)
            return Response({
                'status': 'success',
                'message': 'Verification marked as in progress.',
                'verification_id': verification.id,
                'status': verification.status,
                'verification_notes': verification.verification_notes
            })
        except ValueError as e:
            return Response({
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_verified(self, request, pk=None):
        """Mark a verification as verified"""
        verification = self.get_object()
        notes = request.data.get('verification_notes', '')
        try:
            verification.mark_as_verified(verified_by=request.user, notes=notes)
            return Response({
                'status': 'success',
                'message': 'Verification marked as verified successfully.',
                'verification_id': verification.id,
                'status': verification.status,
                'verification_notes': verification.verification_notes,
                'verified_at': verification.verified_at,
                'expires_at': verification.expires_at
            })
        except ValueError as e:
            return Response({
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_rejected(self, request, pk=None):
        """Mark a verification as rejected with a reason"""
        verification = self.get_object()
        reason = request.data.get('rejection_reason', '')
        notes = request.data.get('verification_notes', '')
        
        if not reason:
            return Response({
                'detail': 'Rejection reason is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            verification.mark_as_rejected(reason=reason, verified_by=request.user)
            if notes:
                verification.verification_notes = notes
                verification.save(update_fields=['verification_notes'])
                
            return Response({
                'status': 'success',
                'message': 'Verification marked as rejected.',
                'verification_id': verification.id,
                'status': verification.status,
                'rejection_reason': verification.rejection_reason,
                'verification_notes': verification.verification_notes
            })
        except ValueError as e:
            return Response({
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def status_summary(self, request):
        """Get summary of verification status counts"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Only administrators can access status summary.'
            }, status=status.HTTP_403_FORBIDDEN)
            
        summary = {
            'status_summary': {},
            'type_summary': {}
        }
        
        # Get status counts
        for status_code, _ in Verification.STATUS_CHOICES:
            count = Verification.objects.filter(status=status_code).count()
            summary['status_summary'][status_code] = count
            
        # Get type counts
        for type_code, _ in Verification.VERIFICATION_TYPE_CHOICES:
            count = Verification.objects.filter(verification_type=type_code).count()
            summary['type_summary'][type_code] = count
            
        return Response(summary)

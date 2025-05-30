from rest_framework import serializers
from .models import Verification
from users.serializers import PublicUserProfileSerializer
import base64
import uuid
from django.core.files.base import ContentFile
from django.utils import timezone

class Base64FileField(serializers.FileField):
    """Custom field for handling base64 encoded files"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:'):
            # Base64 encoded file - decode
            format, filestr = data.split(';base64,') 
            ext = format.split('/')[-1] 
            
            data = ContentFile(
                base64.b64decode(filestr),
                name=f"{uuid.uuid4()}.{ext}"
            )
            
        return super().to_internal_value(data)

class VerificationListSerializer(serializers.ModelSerializer):
    """Serializer for listing verification requests"""
    verification_type_display = serializers.CharField(source='get_verification_type_display', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Verification
        fields = [
            'id', 'verification_type', 'verification_type_display', 'document_type', 
            'document_type_display', 'status', 'status_display', 'submitted_at', 
            'updated_at', 'verified_at'
        ]
        read_only_fields = fields

class VerificationDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed verification request view"""
    verification_type_display = serializers.CharField(source='get_verification_type_display', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user = PublicUserProfileSerializer(read_only=True)
    verified_by = PublicUserProfileSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Verification
        fields = [
            'id', 'user', 'verification_type', 'verification_type_display', 
            'document_type', 'document_type_display', 'document_url', 
            'document_back_url', 'document_number', 'status', 'status_display',
            'verification_notes', 'rejection_reason', 'verified_by', 'verified_at',
            'expires_at', 'is_expired', 'external_reference_id', 'submitted_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_is_expired(self, obj):
        return obj.is_expired()

class VerificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new verification request"""
    document_file = Base64FileField(write_only=True)
    document_back_file = Base64FileField(write_only=True, required=False)
    
    class Meta:
        model = Verification
        fields = [
            'verification_type', 'document_type', 'document_file',
            'document_back_file', 'document_number'
        ]
    
    def validate(self, data):
        # Check if there's already a pending or in_progress verification of this type
        user = self.context['request'].user
        verification_type = data.get('verification_type')
        document_type = data.get('document_type')
        
        # Check for existing verification requests of the same type and document type
        existing_verifications = Verification.objects.filter(
            user=user,
            verification_type=verification_type,
            document_type=document_type,
            status__in=['pending', 'in_progress']
        )
        
        if existing_verifications.exists():
            raise serializers.ValidationError(
                f"You already have a pending verification request for this type. "
                f"Please wait for the current request to be processed or cancel it."
            )
        
        return data
    
    def create(self, validated_data):
        # Extract file fields
        document_file = validated_data.pop('document_file')
        document_back_file = validated_data.pop('document_back_file', None)
        
        # Create verification object
        verification = Verification(
            user=self.context['request'].user,
            document_url=document_file,
            **validated_data
        )
        
        if document_back_file:
            verification.document_back_url = document_back_file
        
        verification.save()
        return verification

class VerificationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating verification request status.
    Primarily used by admins or system processes.
    """
    class Meta:
        model = Verification
        fields = [
            'status', 'verification_notes', 'rejection_reason',
            'external_reference_id', 'verified_by'
        ]
    
    def validate(self, data):
        # Get current status
        instance = self.instance
        new_status = data.get('status')
        
        # Validate status transitions
        if new_status and instance.status != new_status:
            valid_transitions = {
                'pending': ['in_progress', 'verified', 'rejected'],
                'in_progress': ['verified', 'rejected'],
                'verified': ['expired'],  # Usually happens automatically
                'rejected': ['pending'],  # Allowing resubmission
                'expired': ['pending']    # Allowing renewal
            }
            
            if new_status not in valid_transitions.get(instance.status, []):
                raise serializers.ValidationError(
                    f"Invalid status transition from '{instance.status}' to '{new_status}'. "
                    f"Valid transitions are: {', '.join(valid_transitions.get(instance.status, []))}"
                )
            
            # If status is being set to "rejected", require rejection reason
            if new_status == 'rejected' and not data.get('rejection_reason') and not instance.rejection_reason:
                raise serializers.ValidationError(
                    "Rejection reason is required when rejecting a verification request."
                )
                
            # If status is being set to "verified", set verified_at
            if new_status == 'verified':
                data['verified_at'] = timezone.now()
                data['expires_at'] = data['verified_at'] + timezone.timedelta(days=365)
        
        return data
    
    def update(self, instance, validated_data):
        # Special handling for status changes
        new_status = validated_data.get('status')
        
        # Update instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the instance
        instance.save()
        return instance

class VerificationAdminUpdateSerializer(VerificationUpdateSerializer):
    """Extended serializer with additional fields for admin use"""
    
    class Meta(VerificationUpdateSerializer.Meta):
        fields = VerificationUpdateSerializer.Meta.fields + ['verified_by', 'external_reference_id']

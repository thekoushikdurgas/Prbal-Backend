import base64
from datetime import timezone
import uuid
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AccessToken, Verification
from .utils import validate_pin, validate_phone_number, authenticate_user_with_pin, is_pin_strong
# from rest_framework import serializers
# from users.serializers import PublicUserProfileSerializer
import base64
import uuid
from django.core.files.base import ContentFile
from django.utils import timezone

User = get_user_model()
PRBAL_ADMIN_SECRET_CODE = "123"

class EnhancedFileField(serializers.Field):
    """Enhanced file field that can handle URLs, base64, local files, and cloud storage"""
    
    def __init__(self, file_type="auto", max_size=None, **kwargs):
        self.file_type = file_type
        self.max_size = max_size
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        from .utils import UniversalFileConverter
        
        if not data:
            if self.required:
                raise serializers.ValidationError("This field is required.")
            return None
        
        # Convert any input to Django file object
        converted_file = UniversalFileConverter.convert_any_to_file(
            data=data,
            field_name=self.field_name or "file",
            file_type=self.file_type,
            max_size=self.max_size
        )
        
        if not converted_file:
            raise serializers.ValidationError(
                "Unable to process the provided file data. Please check the format and try again."
            )
        
        return converted_file
    
    def to_representation(self, value):
        if not value:
            return None
        
        # Return URL if file has one
        if hasattr(value, 'url'):
            return value.url
        
        # Return filename if available
        if hasattr(value, 'name'):
            return value.name
        
        return str(value)

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Base serializer for user registration without password"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'first_name', 'last_name']
        extra_kwargs = {
            'email': {'required': True}
        }
    
    def create(self, validated_data):
        # Set the user_type based on the specific serializer
        validated_data['user_type'] = self.get_user_type()
        
        # Create the user with the validated data (no password)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            user_type=validated_data['user_type'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', '')
        )
        
        return user
    
    def get_user_type(self):
        """Method to be overridden by subclasses to set the user type"""
        return 'customer'  # Default type


class CustomerRegistrationSerializer(UserRegistrationSerializer):
    """Serializer specifically for customer registration"""
    
    def get_user_type(self):
        return 'customer'


class ProviderRegistrationSerializer(UserRegistrationSerializer):
    """Serializer specifically for service provider registration"""
    skills = serializers.JSONField(required=False)
    
    class Meta(UserRegistrationSerializer.Meta):
        fields = UserRegistrationSerializer.Meta.fields + ['skills']
    
    def get_user_type(self):
        return 'provider'
    
    def create(self, validated_data):
        skills = validated_data.pop('skills', {})
        user = super().create(validated_data)
        user.skills = skills
        user.save()
        return user


class AdminRegistrationSerializer(UserRegistrationSerializer):
    """Serializer specifically for admin registration"""
    admin_code = serializers.CharField(write_only=True, required=True)
    
    class Meta(UserRegistrationSerializer.Meta):
        fields = UserRegistrationSerializer.Meta.fields + ['admin_code']
    
    def validate_admin_code(self, value):
        # You should replace this with a secure code verification system
        # This is just a placeholder for demonstration
        if value != PRBAL_ADMIN_SECRET_CODE:
            raise serializers.ValidationError("Invalid administrator verification code")
        return value
    
    def get_user_type(self):
        return 'admin'
    
    def create(self, validated_data):
        # Remove admin_code as it's not needed for creating the user
        validated_data.pop('admin_code')
        user = super().create(validated_data)
        # Optionally set additional admin privileges
        user.is_staff = True
        user.save()
        return user

# Note: Login serializers removed as they depend on password authentication
# Alternative authentication methods should be implemented (e.g., token-based, OAuth, etc.)

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the user's own profile with all fields"""
    # Enhanced profile picture field that can handle URLs, base64, etc.
    profile_picture_file = EnhancedFileField(file_type="image", required=False, write_only=True, help_text="Profile picture file (any format)")
    profile_picture_link = serializers.URLField(required=False, write_only=True, help_text="URL to profile picture")
    profile_picture_base64 = serializers.CharField(required=False, write_only=True, help_text="Base64 encoded profile picture")
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'first_name', 'last_name', 
                 'user_type', 'profile_picture', 'profile_picture_url', 'bio', 'location', 'is_verified', 
                 'rating', 'balance', 'created_at', 'updated_at',
                 'profile_picture_file', 'profile_picture_link', 'profile_picture_base64']
        read_only_fields = ['id', 'email', 'user_type', 'is_verified', 'rating', 'balance', 'created_at', 'updated_at', 'profile_picture_url']
    
    def get_profile_picture_url(self, obj):
        """Get absolute URL for profile picture"""
        request = self.context.get('request')
        return obj.profile_picture_url(request)
    
    def to_representation(self, instance):
        """Custom representation to ensure consistent profile picture URL formatting"""
        data = super().to_representation(instance)
        
        # Get request from context for absolute URLs
        request = self.context.get('request')
        
        # Ensure consistent profile picture URL formatting with absolute domain
        if instance.profile_picture:
            data['profile_picture_url'] = instance.profile_picture_url(request)
        else:
            data['profile_picture_url'] = None
        
        return data
    
    def update(self, instance, validated_data):
        from .utils import DocumentImageProcessor
        
        # Extract profile picture sources
        profile_picture_file = validated_data.pop('profile_picture_file', None)
        profile_picture_link = validated_data.pop('profile_picture_link', None)
        profile_picture_base64 = validated_data.pop('profile_picture_base64', None)
        
        # Check if any profile picture data was provided
        profile_picture_data = profile_picture_file or profile_picture_link or profile_picture_base64
        
        if profile_picture_data:
            # Process the profile picture using the enhanced processor
            processed_image = DocumentImageProcessor.process_profile_images(profile_picture_data)
            if processed_image:
                validated_data['profile_picture'] = processed_image
            else:
                raise serializers.ValidationError({
                    'profile_picture': 'Failed to process the provided profile picture. Please check the format and try again.'
                })
        
        # Update the instance with the validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class PublicUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for public user profile information"""
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 'profile_picture_url',
                  'bio', 'location', 'user_type', 'is_verified', 'is_email_verified', 'is_phone_verified',
                  'rating', 'total_bookings', 'skills', 'balance', 'created_at']
        read_only_fields = fields  # All fields are read-only for public profile
    
    def get_profile_picture_url(self, obj):
        """Get absolute URL for profile picture"""
        request = self.context.get('request')
        return obj.profile_picture_url(request)
    
    def to_representation(self, instance):
        """Custom representation to ensure consistent profile picture URL formatting"""
        data = super().to_representation(instance)
        
        # Get request from context for absolute URLs
        request = self.context.get('request')
        
        # Ensure consistent profile picture URL formatting with absolute domain
        if instance.profile_picture:
            data['profile_picture_url'] = instance.profile_picture_url(request)
        else:
            data['profile_picture_url'] = None
        
        return data


class CustomerSearchResultSerializer(serializers.ModelSerializer):
    """Serializer for customer search results"""
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 'profile_picture_url',
                  'bio', 'location', 'user_type', 'is_verified', 'balance', 'created_at']
        read_only_fields = fields
    
    def get_profile_picture_url(self, obj):
        """Get absolute URL for profile picture"""
        request = self.context.get('request')
        return obj.profile_picture_url(request)
    
    def to_representation(self, instance):
        """Custom representation to ensure consistent profile picture URL formatting"""
        data = super().to_representation(instance)
        
        # Get request from context for absolute URLs
        request = self.context.get('request')
        
        # Ensure consistent profile picture URL formatting with absolute domain
        if instance.profile_picture:
            data['profile_picture_url'] = instance.profile_picture_url(request)
        else:
            data['profile_picture_url'] = None
        
        return data


class ProviderSearchResultSerializer(serializers.ModelSerializer):
    """Serializer for provider search results"""
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 'profile_picture_url',
                  'bio', 'location', 'user_type', 'is_verified', 'is_email_verified', 'is_phone_verified',
                  'rating', 'total_bookings', 'skills', 'created_at']
        read_only_fields = fields
    
    def get_profile_picture_url(self, obj):
        """Get absolute URL for profile picture"""
        request = self.context.get('request')
        return obj.profile_picture_url(request)
    
    def to_representation(self, instance):
        """Custom representation to ensure consistent profile picture URL formatting"""
        data = super().to_representation(instance)
        
        # Get request from context for absolute URLs
        request = self.context.get('request')
        
        # Ensure consistent profile picture URL formatting with absolute domain
        if instance.profile_picture:
            data['profile_picture_url'] = instance.profile_picture_url(request)
        else:
            data['profile_picture_url'] = None
        
        return data


class AdminSearchResultSerializer(serializers.ModelSerializer):
    """Serializer for admin search results (admin view of any user)"""
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'phone_number',
                  'profile_picture', 'profile_picture_url', 'bio', 'location', 'user_type', 'is_verified',
                  'is_email_verified', 'is_phone_verified', 'is_active', 'is_staff',
                  'rating', 'total_bookings', 'skills', 'balance', 'created_at', 'last_login']
        read_only_fields = fields
    
    def get_profile_picture_url(self, obj):
        """Get absolute URL for profile picture"""
        request = self.context.get('request')
        return obj.profile_picture_url(request)
    
    def to_representation(self, instance):
        """Custom representation to ensure consistent profile picture URL formatting"""
        data = super().to_representation(instance)
        
        # Get request from context for absolute URLs
        request = self.context.get('request')
        
        # Ensure consistent profile picture URL formatting with absolute domain
        if instance.profile_picture:
            data['profile_picture_url'] = instance.profile_picture_url(request)
        else:
            data['profile_picture_url'] = None
        
        return data


class AccessTokenSerializer(serializers.ModelSerializer):
    """Serializer for access token information"""
    user = serializers.StringRelatedField(read_only=True)
    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    
    class Meta:
        model = AccessToken
        fields = ['id', 'user', 'device_type', 'device_type_display', 'device_name', 'ip_address', 
                 'created_at', 'last_used_at', 'last_refreshed_at', 'is_active']
        read_only_fields = fields

# Note: ChangePasswordSerializer removed as password functionality is being removed


# PIN-related Serializers

class PinLoginSerializer(serializers.Serializer):
    """Serializer for phone + PIN authentication"""
    phone_number = serializers.CharField(max_length=15)
    pin = serializers.CharField(max_length=4, min_length=4)
    
    def validate_phone_number(self, value):
        validate_phone_number(value)
        return value
    
    def validate_pin(self, value):
        validate_pin(value)
        return value
    
    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        pin = attrs.get('pin')
        
        if phone_number and pin:
            user = authenticate_user_with_pin(phone_number, pin)
            if not user:
                raise serializers.ValidationError('Invalid phone number or PIN')
            
            if user.is_pin_locked():
                remaining_time = user.get_pin_lock_remaining_time()
                raise serializers.ValidationError(
                    f'PIN is locked due to multiple failed attempts. Try again in {remaining_time} minutes.'
                )
            
            attrs['user'] = user
        
        return attrs


class PinRegistrationSerializer(UserRegistrationSerializer):
    """Enhanced registration serializer with PIN field"""
    pin = serializers.CharField(max_length=4, min_length=4, write_only=True)
    confirm_pin = serializers.CharField(max_length=4, min_length=4, write_only=True)
    
    class Meta(UserRegistrationSerializer.Meta):
        fields = UserRegistrationSerializer.Meta.fields + ['pin', 'confirm_pin']
        extra_kwargs = {
            'email': {'required': True},
            'phone_number': {'required': True}
        }
    
    def validate_phone_number(self, value):
        validate_phone_number(value)
        # Check if phone number already exists
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('Phone number already registered')
        return value
    
    def validate_pin(self, value):
        validate_pin(value)
        return value
    
    def validate_confirm_pin(self, value):
        validate_pin(value)
        return value
    
    def validate(self, attrs):
        pin = attrs.get('pin')
        confirm_pin = attrs.get('confirm_pin')
        
        if pin != confirm_pin:
            raise serializers.ValidationError({'confirm_pin': 'PINs do not match'})
        
        # Check PIN strength (optional - can be made configurable)
        is_strong, message = is_pin_strong(pin)
        if not is_strong:
            raise serializers.ValidationError({'pin': message})
        
        return attrs
    
    def create(self, validated_data):
        pin = validated_data.pop('pin')
        validated_data.pop('confirm_pin')  # Remove confirm_pin as it's not needed
        
        user = super().create(validated_data)
        user.set_pin(pin)
        user.save()
        return user


class ChangePinSerializer(serializers.Serializer):
    """Serializer for changing user PIN"""
    current_pin = serializers.CharField(max_length=4, min_length=4)
    new_pin = serializers.CharField(max_length=4, min_length=4)
    confirm_new_pin = serializers.CharField(max_length=4, min_length=4)
    
    def validate_current_pin(self, value):
        validate_pin(value)
        return value
    
    def validate_new_pin(self, value):
        validate_pin(value)
        return value
    
    def validate_confirm_new_pin(self, value):
        validate_pin(value)
        return value
    
    def validate(self, attrs):
        user = self.context['request'].user
        current_pin = attrs.get('current_pin')
        new_pin = attrs.get('new_pin')
        confirm_new_pin = attrs.get('confirm_new_pin')
        
        # Check if current PIN is correct
        if not user.check_pin(current_pin):
            raise serializers.ValidationError({'current_pin': 'Current PIN is incorrect'})
        
        # Check if new PINs match
        if new_pin != confirm_new_pin:
            raise serializers.ValidationError({'confirm_new_pin': 'New PINs do not match'})
        
        # Check if new PIN is different from current
        if current_pin == new_pin:
            raise serializers.ValidationError({'new_pin': 'New PIN must be different from current PIN'})
        
        # Check PIN strength
        is_strong, message = is_pin_strong(new_pin)
        if not is_strong:
            raise serializers.ValidationError({'new_pin': message})
        
        return attrs


class ResetPinSerializer(serializers.Serializer):
    """Serializer for PIN reset (requires phone verification)"""
    phone_number = serializers.CharField(max_length=15)
    new_pin = serializers.CharField(max_length=4, min_length=4)
    confirm_new_pin = serializers.CharField(max_length=4, min_length=4)
    # Add verification code field when you implement phone verification
    # verification_code = serializers.CharField(max_length=6)
    
    def validate_phone_number(self, value):
        validate_phone_number(value)
        # Check if user exists with this phone number
        if not User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('No user found with this phone number')
        return value
    
    def validate_new_pin(self, value):
        validate_pin(value)
        return value
    
    def validate_confirm_new_pin(self, value):
        validate_pin(value)
        return value
    
    def validate(self, attrs):
        new_pin = attrs.get('new_pin')
        confirm_new_pin = attrs.get('confirm_new_pin')
        
        if new_pin != confirm_new_pin:
            raise serializers.ValidationError({'confirm_new_pin': 'PINs do not match'})
        
        # Check PIN strength
        is_strong, message = is_pin_strong(new_pin)
        if not is_strong:
            raise serializers.ValidationError({'new_pin': message})
        
        return attrs


class PinStatusSerializer(serializers.Serializer):
    """Serializer for PIN status information"""
    is_pin_locked = serializers.SerializerMethodField()
    failed_attempts = serializers.SerializerMethodField()
    remaining_lock_time = serializers.SerializerMethodField()
    pin_last_updated = serializers.SerializerMethodField()
    
    def get_is_pin_locked(self, obj):
        return obj.is_pin_locked()
    
    def get_failed_attempts(self, obj):
        return obj.failed_pin_attempts
    
    def get_remaining_lock_time(self, obj):
        return obj.get_pin_lock_remaining_time()
    
    def get_pin_last_updated(self, obj):
        return obj.pin_updated_at


class UserTypeSerializer(serializers.Serializer):
    """Serializer for user type information based on token"""
    user_id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(read_only=True)
    user_type = serializers.CharField(read_only=True)
    user_type_display = serializers.SerializerMethodField()
    is_customer = serializers.SerializerMethodField()
    is_provider = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    
    def get_user_type_display(self, obj):
        return obj.get_user_type_display()
    
    def get_is_customer(self, obj):
        return obj.user_type == 'customer'
    
    def get_is_provider(self, obj):
        return obj.user_type == 'provider'
    
    def get_is_admin(self, obj):
        return obj.user_type == 'admin'


class UserTypeChangeSerializer(serializers.Serializer):
    """Serializer for user type change requests"""
    to = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_to(self, value):
        """Validate the target user type"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            current_user_type = request.user.user_type
            
            # Prevent changing to the same type
            if value == current_user_type:
                raise serializers.ValidationError(f'You are already a {request.user.get_user_type_display()}')
            
            # Define allowed transitions
            allowed_transitions = {
                'customer': ['provider'],  # Customers can become providers
                'provider': ['customer'],  # Providers can become customers
                'admin': []  # Admins cannot change type (or add specific rules)
            }
            
            if current_user_type not in allowed_transitions:
                raise serializers.ValidationError('Invalid current user type')
            
            if value not in allowed_transitions[current_user_type]:
                raise serializers.ValidationError(
                    f'Cannot change from {request.user.get_user_type_display()} to {dict(User.USER_TYPE_CHOICES)[value]}'
                )
        
        return value
    
    def validate(self, attrs):
        """Additional validation for user type change"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user = request.user
            to_type = attrs.get('to')
            
            # Add any additional business rules here
            # For example, check if user has completed certain requirements
            
            if to_type == 'provider':
                # Example: Check if user has required information to become a provider
                if not user.phone_number:
                    raise serializers.ValidationError(
                        'Phone number is required to become a service provider'
                    )
                    
            elif to_type == 'customer':
                # Example: Check if provider has any pending bookings
                # This would require importing booking models
                pass
        
        return attrs


class UserTypeChangeInfoSerializer(serializers.Serializer):
    """Serializer for user type change information"""
    current_type = serializers.CharField(read_only=True)
    current_type_display = serializers.CharField(read_only=True)
    available_changes = serializers.ListField(read_only=True)
    change_restrictions = serializers.DictField(read_only=True)
    requirements = serializers.DictField(read_only=True)

class Base64FileField(serializers.FileField):
    """Custom field for handling base64 encoded files and other formats"""
    def to_internal_value(self, data):
        # Import the new file processor
        from .utils import UniversalFileConverter
        
        if isinstance(data, str):
            # Use the new universal converter for any string input
            converted_file = UniversalFileConverter.convert_any_to_file(
                data=data,
                field_name=self.field_name or "file",
                file_type="auto"
            )
            if converted_file:
                return converted_file
            else:
                raise serializers.ValidationError("Unable to process the provided file data.")
        
        # If it's already a file object, validate with parent
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
    # Enhanced fields that can handle URLs, base64, local files, and cloud storage
    document_file = EnhancedFileField(file_type="auto", required=False, write_only=True)
    document_back_file = EnhancedFileField(file_type="auto", required=False, write_only=True)
    
    # Alternative fields for different input methods
    document_link = serializers.URLField(required=False, write_only=True, help_text="URL to document")
    document_back_link = serializers.URLField(required=False, write_only=True, help_text="URL to document back")
    document_base64 = serializers.CharField(required=False, write_only=True, help_text="Base64 encoded document")
    document_back_base64 = serializers.CharField(required=False, write_only=True, help_text="Base64 encoded document back")
    
    class Meta:
        model = Verification
        fields = [
            'verification_type', 'document_type', 'document_number',
            'document_file', 'document_back_file',
            'document_link', 'document_back_link', 
            'document_base64', 'document_back_base64'
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
        
        # Validate that at least one document source is provided
        document_sources = [
            data.get('document_file'),
            data.get('document_link'),
            data.get('document_base64')
        ]
        
        if not any(document_sources):
            raise serializers.ValidationError(
                "At least one document must be provided via file upload, URL, or base64 data."
            )
        
        return data
    
    def create(self, validated_data):
        from .utils import DocumentImageProcessor
        
        # Extract all possible document sources
        document_file = validated_data.pop('document_file', None)
        document_back_file = validated_data.pop('document_back_file', None)
        document_link = validated_data.pop('document_link', None)
        document_back_link = validated_data.pop('document_back_link', None)
        document_base64 = validated_data.pop('document_base64', None)
        document_back_base64 = validated_data.pop('document_back_base64', None)
        
        # Determine primary document source
        primary_document_data = document_file or document_link or document_base64
        back_document_data = document_back_file or document_back_link or document_back_base64
        
        # Process documents using the enhanced processor
        primary_file, back_file = DocumentImageProcessor.process_verification_documents(
            primary_document=primary_document_data,
            back_document=back_document_data,
            field_prefix="verification_doc"
        )
        
        if not primary_file:
            raise serializers.ValidationError(
                "Failed to process the primary document. Please check the format and try again."
            )
        
        # Create verification object
        verification = Verification(
            user=self.context['request'].user,
            document_url=primary_file,
            **validated_data
        )
        
        if back_file:
            verification.document_back_url = back_file
        
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

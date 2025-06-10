from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AccessToken
from .utils import validate_pin, validate_phone_number, authenticate_user_with_pin, is_pin_strong

User = get_user_model()
PRBAL_ADMIN_SECRET_CODE = "123"

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
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'first_name', 'last_name', 
                 'user_type', 'profile_picture', 'bio', 'location', 'is_verified', 
                 'rating', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'email', 'user_type', 'is_verified', 'rating', 'balance', 'created_at', 'updated_at']

class PublicUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the public view of a user profile"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 
                 'bio', 'location', 'user_type', 'is_verified', 'rating', 'created_at']
        read_only_fields = fields  # All fields are read-only in public view


class CustomerSearchResultSerializer(serializers.ModelSerializer):
    """Serializer for customer search results"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture',
                 'bio', 'location', 'user_type', 'is_verified', 'created_at']
        read_only_fields = fields


class ProviderSearchResultSerializer(serializers.ModelSerializer):
    """Serializer for service provider search results"""
    services_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture',
                 'bio', 'location', 'user_type', 'is_verified', 'rating', 
                 'skills', 'total_bookings', 'services_count', 'created_at']
        read_only_fields = fields
    
    def get_services_count(self, obj):
        # Import here to avoid circular imports
        from api.models import Service
        return Service.objects.filter(service_provider=obj).count()


class AdminSearchResultSerializer(serializers.ModelSerializer):
    """Serializer for admin search results with extended information"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'first_name', 'last_name',
                 'profile_picture', 'bio', 'location', 'user_type', 'is_verified',
                 'is_email_verified', 'is_phone_verified', 'rating', 'total_bookings',
                 'balance', 'created_at', 'updated_at', 'last_login', 'is_active']
        read_only_fields = fields


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

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()
PRBAL_ADMIN_SECRET_CODE = "123"
class UserRegistrationSerializer(serializers.ModelSerializer):
    """Base serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'password', 'password_confirm', 'first_name', 'last_name']
        extra_kwargs = {
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
            
        return attrs
    
    def create(self, validated_data):
        # Remove password_confirm as it's not needed for creating the user
        validated_data.pop('password_confirm')
        
        # Set the user_type based on the specific serializer
        validated_data['user_type'] = self.get_user_type()
        
        # Create the user with the validated data
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
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

class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    password = serializers.CharField(style={'input_type': 'password'})
    user_type = serializers.CharField(required=False)
    
    def validate(self, attrs):
        # Check if at least one identifier field is provided
        identifier_fields = ['username', 'email', 'phone_number']
        if not any(attrs.get(field) for field in identifier_fields):
            raise serializers.ValidationError("Must include either 'username', 'email' or 'phone_number'")
        
        # Try to authenticate with provided credentials
        user = None
        
        if attrs.get('username'):
            user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        elif attrs.get('email'):
            try:
                user_obj = User.objects.get(email=attrs.get('email'))
                user = authenticate(username=user_obj.username, password=attrs.get('password'))
            except User.DoesNotExist:
                pass
        elif attrs.get('phone_number'):
            try:
                user_obj = User.objects.get(phone_number=attrs.get('phone_number'))
                user = authenticate(username=user_obj.username, password=attrs.get('password'))
            except User.DoesNotExist:
                pass
        
        if not user:
            raise serializers.ValidationError("Unable to log in with provided credentials.")
        
        # Check if the user type is specified and matches
        if attrs.get('user_type') and user.user_type != attrs.get('user_type'):
            raise serializers.ValidationError(f"User is not registered as a {attrs.get('user_type')}")
        
        attrs['user'] = user
        return attrs


class CustomerLoginSerializer(UserLoginSerializer):
    """Serializer for customer login"""
    
    def validate(self, attrs):
        attrs['user_type'] = 'customer'
        return super().validate(attrs)


class ProviderLoginSerializer(UserLoginSerializer):
    """Serializer for service provider login"""
    
    def validate(self, attrs):
        attrs['user_type'] = 'provider'
        return super().validate(attrs)


class AdminLoginSerializer(UserLoginSerializer):
    """Serializer for admin login"""
    
    def validate(self, attrs):
        attrs['user_type'] = 'admin'
        return super().validate(attrs)

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


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change.
    Requires the user to be authenticated.
    """
    old_password = serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True, write_only=True, style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Your old password was entered incorrectly. Please enter it again."
            )
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password_confirm": "The two new password fields didn't match."}
            )
        
        try:
            validate_password(data['new_password'], user=self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        # Consider: from django.contrib.auth import update_session_auth_hash
        # update_session_auth_hash(self.context['request'], user)
        return user

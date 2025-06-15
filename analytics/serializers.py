from rest_framework import serializers
from django.contrib.auth import get_user_model
from services.models import Service, ServiceCategory, ServiceSubCategory
from bookings.models import Booking
from payments.models import Payment
from bids.models import Bid

User = get_user_model()


class AdminUserCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin user creation and updates"""
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'user_type', 'is_active', 'is_verified'
        ]
        # Example: To make email read-only during update, you could add:
        # extra_kwargs = {'email': {'read_only': True, 'required': False}}
        # However, for admin, allowing email change might be acceptable.

    def create(self, validated_data):
        password_data = validated_data.pop('password', None)
        if not password_data:
            raise serializers.ValidationError({'password': 'Password is required for new users.'})

        user = User(**validated_data)
        user.set_password(password_data)

        if user.user_type == 'admin':
            user.is_staff = True
            # Consider if admin type should also imply is_superuser=True
            # user.is_superuser = True 
        else:
            user.is_staff = False
            user.is_superuser = False # Ensure non-admins are not superusers

        user.save()
        return user

    def update(self, instance, validated_data):
        password_data = validated_data.pop('password', None)

        # Update instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password_data:
            instance.set_password(password_data)

        # Adjust staff/superuser status if user_type is changed
        if 'user_type' in validated_data:
            if instance.user_type == 'admin':
                instance.is_staff = True
                # user.is_superuser = True
            else:
                instance.is_staff = False
                instance.is_superuser = False
        
        instance.save()
        return instance


class OverviewStatsSerializer(serializers.Serializer):
    """Serializer for overview analytics dashboard"""
    # Platform statistics
    total_users = serializers.IntegerField()
    total_providers = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    total_services = serializers.IntegerField()
    total_bookings = serializers.IntegerField()
    total_completed_bookings = serializers.IntegerField()
    total_cancelled_bookings = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Time-based stats
    active_users_last_30_days = serializers.IntegerField()
    new_users_last_30_days = serializers.IntegerField()
    bookings_last_30_days = serializers.IntegerField()
    revenue_last_30_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Growth metrics
    user_growth_rate = serializers.FloatField()
    booking_growth_rate = serializers.FloatField()
    revenue_growth_rate = serializers.FloatField()
    
    # Top categories
    top_categories = serializers.ListField(
        child=serializers.DictField()
    )
    
    # User activity timeline
    user_activity_timeline = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Booking status distribution
    booking_status_distribution = serializers.DictField()

class EarningsAnalyticsSerializer(serializers.Serializer):
    """Serializer for provider earnings analytics"""
    # Overall earnings
    total_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    earnings_last_30_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    earnings_last_7_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Provider statistics
    total_providers = serializers.IntegerField()
    active_providers_last_30_days = serializers.IntegerField()
    avg_provider_earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Earnings by category
    earnings_by_category = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Earnings timeline
    earnings_timeline = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Top earning providers
    top_providers = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Commission statistics
    platform_commission_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_commission_rate = serializers.FloatField()

class AdminUserListSerializer(serializers.ModelSerializer):
    """Serializer for admin user listing"""
    booking_count = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_earned = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'user_type', 'is_verified', 'date_joined', 'last_login',
            'is_active', 'booking_count', 'total_spent', 'total_earned'
        ]

class AdminServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin service creation and updates"""
    # Ensure provider, category, and subcategories can be set by ID
    # provider = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # category = serializers.PrimaryKeyRelatedField(queryset=ServiceCategory.objects.all())
    # subcategories = serializers.PrimaryKeyRelatedField(queryset=ServiceSubCategory.objects.all(), many=True, required=False)

    # Service model has 'name' and 'hourly_rate'. List serializer uses 'title' and 'price'.
    # We will use actual model field names here for clarity in CUD operations.

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'provider', 'category', 'subcategories',
            'tags', 'hourly_rate', 'pricing_options', 'currency', 'min_hours',
            'max_hours', 'availability', 'location', 'latitude', 'longitude',
            'required_tools', 'status', 'is_featured',
            # Read-only fields from model's auto_now_add/auto_now are implicitly handled
            # 'created_at', 'updated_at' 
        ]
        read_only_fields = ['id'] # 'created_at', 'updated_at' are already read-only by default

    # Optional: Add custom validation or create/update logic if needed
    # For example, to ensure provider is of 'provider' user_type:
    # def validate_provider(self, value):
    #     if value.user_type != 'provider':
    #         raise serializers.ValidationError("Service provider must be a user with 'provider' type.")
    #     return value

class AdminServiceListSerializer(serializers.ModelSerializer):
    """Serializer for admin service listing"""
    provider_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    booking_count = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'title', 'provider', 'provider_name', 'category', 
            'category_name', 'price', 'status', 'is_featured',
            'created_at', 'booking_count', 'total_revenue'
        ]
        
    def get_provider_name(self, obj):
        return f"{obj.provider.first_name} {obj.provider.last_name}" if obj.provider else "Unknown"
        
    def get_category_name(self, obj):
        return obj.category.name if obj.category else "Uncategorized"

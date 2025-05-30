from rest_framework import serializers
from django.contrib.auth import get_user_model
from api.models import Service
from bookings.models import Booking
from payments.models import Payment
from bids.models import Bid

User = get_user_model()

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

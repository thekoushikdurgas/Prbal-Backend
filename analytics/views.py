from django.shortcuts import render
from django.db.models import Count, Sum, F, Q, Avg, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

from services.models import Service, ServiceCategory
from bookings.models import Booking
from payments.models import Payment
from bids.models import Bid
from .serializers import (
    OverviewStatsSerializer,
    EarningsAnalyticsSerializer,
    AdminUserListSerializer,
    AdminUserCreateUpdateSerializer,  # Added import
    AdminServiceListSerializer,
    AdminServiceCreateUpdateSerializer # Added import for service CUD
)

User = get_user_model()

class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users to access the view"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == 'admin'

CACHE_TTL_ANALYTICS = 60 * 15  # 15 minutes

@method_decorator(cache_page(CACHE_TTL_ANALYTICS), name='dispatch')
class AnalyticsOverviewView(APIView):
    """API endpoint for getting platform overview analytics dashboard"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request, format=None):
        # Get time ranges for filtering
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)
        ninety_days_ago = now - timedelta(days=90)
        
        # Calculate platform statistics
        total_users = User.objects.count()
        total_providers = User.objects.filter(user_type='provider').count()
        total_customers = User.objects.filter(user_type='customer').count()
        total_services = Service.objects.count()
        total_bookings = Booking.objects.count()
        total_completed_bookings = Booking.objects.filter(status='completed').count()
        total_cancelled_bookings = Booking.objects.filter(status='cancelled').count()
        
        # Calculate payments and revenue
        payment_stats = Payment.objects.filter(
            status='completed'
        ).aggregate(
            total_revenue=Sum('amount')
        )
        
        total_revenue = payment_stats.get('total_revenue') or 0
        
        # Calculate time-based stats
        active_users_last_30_days = User.objects.filter(
            last_login__gte=thirty_days_ago
        ).count()
        
        new_users_last_30_days = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).count()
        
        bookings_last_30_days = Booking.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        revenue_last_30_days = Payment.objects.filter(
            status='completed',
            created_at__gte=thirty_days_ago
        ).aggregate(
            revenue=Sum('amount')
        ).get('revenue') or 0
        
        # Calculate growth metrics
        prev_30_days_new_users = User.objects.filter(
            date_joined__gte=sixty_days_ago,
            date_joined__lt=thirty_days_ago
        ).count()
        
        prev_30_days_bookings = Booking.objects.filter(
            created_at__gte=sixty_days_ago,
            created_at__lt=thirty_days_ago
        ).count()
        
        prev_30_days_revenue = Payment.objects.filter(
            status='completed',
            created_at__gte=sixty_days_ago,
            created_at__lt=thirty_days_ago
        ).aggregate(
            revenue=Sum('amount')
        ).get('revenue') or 0
        
        # Calculate growth rates (avoid division by zero)
        user_growth_rate = (new_users_last_30_days / prev_30_days_new_users - 1) * 100 if prev_30_days_new_users > 0 else 0
        booking_growth_rate = (bookings_last_30_days / prev_30_days_bookings - 1) * 100 if prev_30_days_bookings > 0 else 0
        revenue_growth_rate = (revenue_last_30_days / prev_30_days_revenue - 1) * 100 if prev_30_days_revenue > 0 else 0
        
        # Get top categories
        top_categories = ServiceCategory.objects.annotate(
            service_count=Count('services'),
            booking_count=Count('services__bookings'),
            revenue=Sum('services__bookings__amount')
        ).values(
            'id', 'name', 'service_count', 'booking_count', 'revenue'
        ).order_by('-booking_count')[:5]
        
        # Create user activity timeline (last 30 days)
        user_activity = []
        for i in range(30, 0, -1):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            active_users = User.objects.filter(last_login__range=(day_start, day_end)).count()
            new_users = User.objects.filter(date_joined__range=(day_start, day_end)).count()
            
            user_activity.append({
                'date': day_start.date().isoformat(),
                'active_users': active_users,
                'new_users': new_users
            })
        
        # Get booking status distribution
        booking_status_counts = Booking.objects.values('status').annotate(
            count=Count('id')
        )
        
        booking_status_distribution = {}
        for item in booking_status_counts:
            booking_status_distribution[item['status']] = item['count']
        
        # Prepare and return the serialized data
        overview_data = {
            'total_users': total_users,
            'total_providers': total_providers,
            'total_customers': total_customers,
            'total_services': total_services,
            'total_bookings': total_bookings,
            'total_completed_bookings': total_completed_bookings,
            'total_cancelled_bookings': total_cancelled_bookings,
            'total_revenue': total_revenue,
            'active_users_last_30_days': active_users_last_30_days,
            'new_users_last_30_days': new_users_last_30_days,
            'bookings_last_30_days': bookings_last_30_days,
            'revenue_last_30_days': revenue_last_30_days,
            'user_growth_rate': user_growth_rate,
            'booking_growth_rate': booking_growth_rate,
            'revenue_growth_rate': revenue_growth_rate,
            'top_categories': top_categories,
            'user_activity_timeline': user_activity,
            'booking_status_distribution': booking_status_distribution
        }
        
        serializer = OverviewStatsSerializer(overview_data)
        return Response(serializer.data)

class EarningsAnalyticsView(APIView):
    """API endpoint for getting provider earnings analytics"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get(self, request, format=None):
        # Get time ranges for filtering
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)
        
        # Calculate overall earnings (based on completed payments to providers)
        earnings_stats = Payment.objects.filter(
            status='completed',
            payment_type='provider_payout'
        ).aggregate(
            total_earnings=Sum('amount'),
            earnings_last_30_days=Sum('amount', filter=Q(created_at__gte=thirty_days_ago)),
            earnings_last_7_days=Sum('amount', filter=Q(created_at__gte=seven_days_ago))
        )
        
        total_earnings = earnings_stats.get('total_earnings') or 0
        earnings_last_30_days = earnings_stats.get('earnings_last_30_days') or 0
        earnings_last_7_days = earnings_stats.get('earnings_last_7_days') or 0
        
        # Provider statistics
        total_providers = User.objects.filter(user_type='provider').count()
        active_providers_last_30_days = User.objects.filter(
            user_type='provider',
            last_login__gte=thirty_days_ago
        ).count()
        
        # Calculate average provider earnings (avoid division by zero)
        avg_provider_earnings = total_earnings / total_providers if total_providers > 0 else 0
        
        # Get earnings by category
        earnings_by_category = ServiceCategory.objects.annotate(
            total_earnings=Sum('services__bookings__payment__amount',
                              filter=Q(services__bookings__payment__payment_type='provider_payout',
                                       services__bookings__payment__status='completed'))
        ).values(
            'id', 'name', 'total_earnings'
        ).order_by('-total_earnings')[:10]
        
        # Clean up None values in earnings_by_category
        for category in earnings_by_category:
            if category['total_earnings'] is None:
                category['total_earnings'] = 0
        
        # Create earnings timeline (last 30 days)
        earnings_timeline = []
        for i in range(30, 0, -1):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            daily_earnings = Payment.objects.filter(
                payment_type='provider_payout',
                status='completed',
                created_at__range=(day_start, day_end)
            ).aggregate(amount=Sum('amount')).get('amount') or 0
            
            earnings_timeline.append({
                'date': day_start.date().isoformat(),
                'earnings': daily_earnings
            })
        
        # Get top earning providers
        top_providers = User.objects.filter(
            user_type='provider'
        ).annotate(
            total_earned=Sum('provider_bookings__payment__amount',
                           filter=Q(provider_bookings__payment__payment_type='provider_payout',
                                    provider_bookings__payment__status='completed'))
        ).values(
            'id', 'username', 'first_name', 'last_name', 'total_earned'
        ).order_by('-total_earned')[:10]
        
        # Clean up None values in top_providers
        for provider in top_providers:
            if provider['total_earned'] is None:
                provider['total_earned'] = 0
        
        # Calculate commission statistics
        platform_commission_stats = Payment.objects.filter(
            payment_type='platform_fee',
            status='completed'
        ).aggregate(
            platform_commission_total=Sum('amount')
        )
        
        platform_commission_total = platform_commission_stats.get('platform_commission_total') or 0
        
        # Calculate average commission rate
        total_transactions = Payment.objects.filter(
            status='completed'
        ).count()
        
        avg_commission_rate = Payment.objects.filter(
            payment_type='platform_fee',
            status='completed'
        ).aggregate(
            avg_rate=Avg('commission_rate')
        ).get('avg_rate') or 0
        
        # Prepare and return the serialized data
        earnings_data = {
            'total_earnings': total_earnings,
            'earnings_last_30_days': earnings_last_30_days,
            'earnings_last_7_days': earnings_last_7_days,
            'total_providers': total_providers,
            'active_providers_last_30_days': active_providers_last_30_days,
            'avg_provider_earnings': avg_provider_earnings,
            'earnings_by_category': earnings_by_category,
            'earnings_timeline': earnings_timeline,
            'top_providers': top_providers,
            'platform_commission_total': platform_commission_total,
            'avg_commission_rate': avg_commission_rate
        }

class AdminUserViewSet(viewsets.ModelViewSet):
    """API endpoint for listing, creating, updating, and deleting users (admin only)"""
    # queryset attribute is removed as get_queryset handles it dynamically.
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return AdminUserCreateUpdateSerializer
        return AdminUserListSerializer # For list and retrieve

    def get_queryset(self):
        queryset = super().get_queryset() # Start with the base queryset from ModelViewSet

        # Annotate with additional stats required by AdminUserListSerializer
        # Ensure 'customer_bookings' and 'provider_bookings' are correct related_names in your User model
        # or adjust these paths. Assuming Booking model has an 'amount' field.
        queryset = queryset.annotate(
            booking_count=Count('customer_bookings', distinct=True) + Count('provider_bookings', distinct=True),
            total_spent=Coalesce(
                Sum('customer_bookings__amount'),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
            ),
            total_earned=Coalesce(
                Sum('provider_bookings__amount'),
                Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
            )
        )
        
        # Apply ordering. It's often good to order after annotations if annotations affect order.
        queryset = queryset.order_by('-date_joined')

        # Apply filters if provided in query parameters
        user_type = self.request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
            
        is_verified_param = self.request.query_params.get('is_verified')
        if is_verified_param is not None:
            is_verified = str(is_verified_param).lower() == 'true'
            queryset = queryset.filter(is_verified=is_verified)
            
        is_active_param = self.request.query_params.get('is_active')
        if is_active_param is not None:
            is_active = str(is_active_param).lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
            
        search = self.request.query_params.get('search')
        if search:
            # Using SearchQuery with 'websearch' type allows for more flexible user input
            # e.g., "john doe" will search for john AND doe, "john or doe" for john OR doe.
            # It also handles stemming based on the 'config' used when creating the SearchVector.
            query = SearchQuery(search, search_type='websearch', config='english')
            # Optional: Rank results by relevance
            # queryset = queryset.annotate(
            #     rank=SearchRank(F('search_vector'), query)
            # ).filter(search_vector=query).order_by('-rank', '-date_joined')
            # Simpler filtering without explicit ranking, relying on default ordering or '-date_joined':
            queryset = queryset.filter(search_vector=query)
            
        return queryset

class AdminServiceViewSet(viewsets.ModelViewSet):
    """API endpoint for listing, creating, updating, and deleting services (admin only)"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """Annotate services with booking count and total revenue for list/retrieve views, and apply filters."""
        queryset = Service.objects.all()

        # Apply filters if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        provider_id = self.request.query_params.get('provider')
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
            
        is_featured_param = self.request.query_params.get('is_featured')
        if is_featured_param is not None:
            is_featured = is_featured_param.lower() == 'true'
            queryset = queryset.filter(is_featured=is_featured)
            
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search) |
                Q(provider__username__icontains=search) |
                Q(provider__first_name__icontains=search) |
                Q(provider__last_name__icontains=search)
            )

        # Annotate, select related, and order
        # This queryset is primarily for AdminServiceListSerializer when listing/retrieving
        # For create/update/delete, the base queryset from ModelViewSet is used directly with AdminServiceCreateUpdateSerializer
        queryset = queryset.annotate(
            booking_count=Coalesce(Count('bookings', distinct=True), Value(0)), # distinct=True might be important depending on relations
            total_revenue=Coalesce(Sum('bookings__payment__amount', filter=Q(bookings__payment__status='completed')), Value(0.0), output_field=DecimalField())
        ).select_related('provider', 'category').order_by('-created_at')
        
        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return AdminServiceCreateUpdateSerializer
        return AdminServiceListSerializer

    # Optional: Add perform_create, perform_update, perform_destroy methods for custom logic
    # For example, to set the provider automatically if not provided (though admin should specify):
    # def perform_create(self, serializer):
    #     # Example: if provider is not in request.data, set to request.user if admin is also a provider
    #     # This is generally not needed for admin viewsets where admin explicitly sets fields.
    #     serializer.save()


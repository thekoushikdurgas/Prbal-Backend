from django.shortcuts import render
from django.db.models import Count, Sum, F, Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from api.models import Service, ServiceCategory
from bookings.models import Booking
from payments.models import Payment
from bids.models import Bid
from .serializers import (
    OverviewStatsSerializer,
    EarningsAnalyticsSerializer,
    AdminUserListSerializer,
    AdminServiceListSerializer
)

User = get_user_model()

class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users to access the view"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == 'admin'

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
        
        serializer = EarningsAnalyticsSerializer(earnings_data)
        return Response(serializer.data)

class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing and viewing all users (admin only)"""
    queryset = User.objects.all()
    serializer_class = AdminUserListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # Annotate with additional stats
        queryset = queryset.annotate(
            booking_count=Count('customer_bookings', distinct=True) + Count('provider_bookings', distinct=True),
            total_spent=Sum('customer_bookings__amount', distinct=True),
            total_earned=Sum('provider_bookings__amount', distinct=True)
        )
        
        # Apply filters if provided
        user_type = self.request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
            
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified == 'true')
            
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
            
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
            
        return queryset

class AdminServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing and viewing all services (admin only)"""
    queryset = Service.objects.all()
    serializer_class = AdminServiceListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = Service.objects.all().order_by('-created_at')
        
        # Annotate with additional stats
        queryset = queryset.annotate(
            booking_count=Count('bookings', distinct=True),
            total_revenue=Sum('bookings__amount', distinct=True)
        )
        
        # Apply filters if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
            
        is_featured = self.request.query_params.get('is_featured')
        if is_featured is not None:
            queryset = queryset.filter(is_featured=is_featured == 'true')
            
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search) |
                Q(provider__username__icontains=search) |
                Q(provider__first_name__icontains=search) |
                Q(provider__last_name__icontains=search)
            )
            
        return queryset

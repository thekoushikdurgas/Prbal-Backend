"""
Custom admin dashboard for monitoring and management of the Prbal service marketplace.
Provides system health metrics, business KPIs, and operational tools.
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from users.models import User
from bids.models import Bid
from bookings.models import Booking
from reviews.models import Review
from payments.models import Payment
from services.models import Service, ServiceCategory, ServiceSubCategory, ServiceRequest

class AdminDashboard:
    """
    Dashboard for monitoring system health and business metrics
    """
    
    @staticmethod
    def get_admin_urls():
        """Return custom admin URLs for the dashboard"""
        urls = [
            path('dashboard/', AdminDashboard.dashboard_view, name='admin_dashboard'),
            path('system-health/', AdminDashboard.system_health_view, name='admin_system_health'),
            path('business-metrics/', AdminDashboard.business_metrics_view, name='admin_business_metrics'),
        ]
        return urls
    
    @staticmethod
    def dashboard_view(request):
        """Main dashboard view showing key metrics and system health"""
        # User stats
        total_users = User.objects.count()
        new_users_today = User.objects.filter(
            date_joined__gte=timezone.now().replace(hour=0, minute=0, second=0)
        ).count()
        
        # Service stats
        total_services = Service.objects.count()
        active_services = Service.objects.filter(status='active').count()
        pending_services = Service.objects.filter(status='pending').count()
        inactive_services = Service.objects.filter(status='inactive').count()
        
        # Service Category stats
        total_categories = ServiceCategory.objects.count()
        active_categories = ServiceCategory.objects.filter(is_active=True).count()
        categories_with_services = ServiceCategory.objects.annotate(
            service_count=Count('services')
        ).filter(service_count__gt=0).count()
        
        # Service Request stats
        total_requests = ServiceRequest.objects.count()
        open_requests = ServiceRequest.objects.filter(status='open').count()
        fulfilled_requests = ServiceRequest.objects.filter(status='fulfilled').count()
        expired_requests = ServiceRequest.objects.filter(status='expired').count()
        in_progress_requests = ServiceRequest.objects.filter(status='in_progress').count()
        
        # Service provider stats
        provider_count = User.objects.filter(user_type='provider').count()
        active_providers = User.objects.filter(
            user_type='provider',
            services__status='active'
        ).distinct().count()
        
        # Customer stats
        customer_count = User.objects.filter(user_type='customer').count()
        customers_with_requests = User.objects.filter(
            user_type='customer',
            service_requests__isnull=False
        ).distinct().count()
        
        # Bid stats
        total_bids = Bid.objects.count()
        bids_today = Bid.objects.filter(
            created_at__gte=timezone.now().replace(hour=0, minute=0, second=0)
        ).count()
        
        # Booking stats
        total_bookings = Booking.objects.count()
        bookings_today = Booking.objects.filter(
            created_at__gte=timezone.now().replace(hour=0, minute=0, second=0)
        ).count()
        
        # Payment stats
        total_payments = Payment.objects.count()
        payments_today = Payment.objects.filter(
            created_at__gte=timezone.now().replace(hour=0, minute=0, second=0)
        ).count()
        
        # Revenue stats (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        revenue_30_days = Payment.objects.filter(
            status='completed',
            created_at__gte=thirty_days_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate bid conversion rate
        total_accepted_bids = Bid.objects.filter(status='accepted').count()
        bid_conversion_rate = (total_accepted_bids / total_bids * 100) if total_bids > 0 else 0
        
        # Get review stats
        avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg'] or 0
        
        context = {
            'title': 'Prbal Admin Dashboard',
            'total_users': total_users,
            'new_users_today': new_users_today,
            'total_services': total_services,
            'active_services': active_services,
            'total_bids': total_bids,
            'bids_today': bids_today,
            'total_bookings': total_bookings,
            'bookings_today': bookings_today,
            'total_payments': total_payments,
            'payments_today': payments_today,
            'revenue_30_days': revenue_30_days,
            'bid_conversion_rate': bid_conversion_rate,
            'avg_rating': avg_rating,
        }
        
        return render(request, 'admin/dashboard.html', context)
    
    @staticmethod
    def system_health_view(request):
        """View for monitoring system health and performance"""
        # Database connection status
        from django.db import connection
        db_status = "Connected"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            db_status = f"Error: {str(e)}"
        
        # Check Redis connection
        from django.core.cache import cache
        redis_status = "Connected"
        try:
            cache.set('health_check', 'ok', 10)
            cache_value = cache.get('health_check')
            if cache_value != 'ok':
                redis_status = "Error: Cache value not set correctly"
        except Exception as e:
            redis_status = f"Error: {str(e)}"
        
        # Get recent API response times (if available)
        from django.core.cache import cache
        recent_api_times = cache.get('recent_api_response_times', [])
        
        # Check disk usage
        import shutil
        disk_usage = shutil.disk_usage('/')
        disk_percent = disk_usage.used / disk_usage.total * 100
        
        # CPU load
        import os
        try:
            load_avg = os.getloadavg()
        except AttributeError:
            # Windows doesn't support getloadavg
            load_avg = (0, 0, 0)
        
        context = {
            'title': 'System Health',
            'db_status': db_status,
            'redis_status': redis_status,
            'disk_usage': {
                'total_gb': disk_usage.total / (1024**3),
                'used_gb': disk_usage.used / (1024**3),
                'free_gb': disk_usage.free / (1024**3),
                'percent': disk_percent,
            },
            'load_avg': load_avg,
            'recent_api_times': recent_api_times,
        }
        
        return render(request, 'admin/system_health.html', context)
    
    @staticmethod
    def business_metrics_view(request):
        """View for business KPIs and analytics"""
        # Time range filters
        last_30_days = timezone.now() - timedelta(days=30)
        last_7_days = timezone.now() - timedelta(days=7)
        
        # Calculate bid conversion rate over time
        bid_conversion_30d = (
            Bid.objects.filter(status='accepted', created_at__gte=last_30_days).count() /
            max(Bid.objects.filter(created_at__gte=last_30_days).count(), 1)
        ) * 100
        
        bid_conversion_7d = (
            Bid.objects.filter(status='accepted', created_at__gte=last_7_days).count() /
            max(Bid.objects.filter(created_at__gte=last_7_days).count(), 1)
        ) * 100
        
        # User growth
        new_users_30d = User.objects.filter(date_joined__gte=last_30_days).count()
        new_users_7d = User.objects.filter(date_joined__gte=last_7_days).count()
        
        # Revenue stats
        revenue_30d = Payment.objects.filter(
            status='completed',
            created_at__gte=last_30_days
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        revenue_7d = Payment.objects.filter(
            status='completed',
            created_at__gte=last_7_days
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Popular categories
        popular_categories = ServiceCategory.objects.annotate(
            service_count=Count('service')
        ).order_by('-service_count')[:5]
        
        # Top rated services
        top_services = Service.objects.annotate(
            avg_rating=Avg('review__rating'),
            review_count=Count('review')
        ).filter(review_count__gt=0).order_by('-avg_rating')[:10]
        
        context = {
            'title': 'Business Metrics',
            'bid_conversion_30d': bid_conversion_30d,
            'bid_conversion_7d': bid_conversion_7d,
            'new_users_30d': new_users_30d,
            'new_users_7d': new_users_7d,
            'revenue_30d': revenue_30d,
            'revenue_7d': revenue_7d,
            'popular_categories': popular_categories,
            'top_services': top_services,
        }
        
        return render(request, 'admin/business_metrics.html', context)

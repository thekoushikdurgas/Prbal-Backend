from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnalyticsOverviewView,
    EarningsAnalyticsView,
    AdminUserViewSet,
    AdminServiceViewSet
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')
router.register(r'admin/services', AdminServiceViewSet, basename='admin-services')

urlpatterns = [
    # Analytics dashboard endpoints
    path('overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('earnings/', EarningsAnalyticsView.as_view(), name='earnings-analytics'),
    
    # Include router URLs (admin endpoints)
    path('', include(router.urls)),
]

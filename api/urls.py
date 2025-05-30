from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Import your viewsets here
from .views import ServiceCategoryViewSet, ServiceSubCategoryViewSet, ServiceViewSet, ServiceRequestViewSet

router = DefaultRouter()
# Register your viewsets here
router.register(r'v1/services/categories', ServiceCategoryViewSet, basename='service-category')
router.register(r'v1/services/subcategories', ServiceSubCategoryViewSet, basename='service-subcategory')
router.register(r'v1/services', ServiceViewSet, basename='service')
router.register(r'v1/service-requests', ServiceRequestViewSet, basename='service-request')

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints using router
    path('', include(router.urls)),
]

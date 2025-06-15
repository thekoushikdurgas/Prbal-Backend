from django.urls import path

# Import your viewsets here
from .views import ServiceCategoryViewSet, ServiceSubCategoryViewSet, ServiceViewSet, ServiceRequestViewSet

urlpatterns = [
    # API endpoints using router
    path('categories/', ServiceCategoryViewSet.as_view({'get': 'list'}), name='service-categories'),
    path('subcategories/', ServiceSubCategoryViewSet.as_view({'get': 'list'}), name='service-subcategories'),
    path('', ServiceViewSet.as_view({'get': 'list'}), name='service-statistics'),
    path('requests/', ServiceRequestViewSet.as_view({'get': 'list'}), name='service-requests'),
]

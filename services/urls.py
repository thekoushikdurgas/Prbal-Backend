from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import your viewsets here
from .views import ServiceCategoryViewSet, ServiceSubCategoryViewSet, ServiceViewSet, ServiceRequestViewSet

# Debug: Print statement to verify URL loading
print("🔧 DEBUG: Loading services app URLs with proper router configuration")

# Create router and register viewsets
router = DefaultRouter()

# Debug: Log each viewset registration  
print("📝 DEBUG: Registering ServiceCategoryViewSet at 'categories'")
router.register(r'categories', ServiceCategoryViewSet, basename='service-category')

print("📝 DEBUG: Registering ServiceSubCategoryViewSet at 'subcategories'")
router.register(r'subcategories', ServiceSubCategoryViewSet, basename='service-subcategory')

print("📝 DEBUG: Registering ServiceViewSet at 'services' (base path)")
router.register(r'services', ServiceViewSet, basename='service')

print("📝 DEBUG: Registering ServiceRequestViewSet at 'requests'")
router.register(r'requests', ServiceRequestViewSet, basename='service-request')

# Debug: Print all registered routes
print("🔍 DEBUG: Router registered routes:")
for pattern in router.urls:
    print(f"   - {pattern.pattern}")

urlpatterns = [
    # Include all router-generated URLs
    path('', include(router.urls)),
]

# Debug: Confirm URL pattern setup completion
print("✅ DEBUG: Services app URL configuration completed successfully")
print(f"📊 DEBUG: Total URL patterns generated: {len(router.urls)}")

"""
ENDPOINT MAPPING REFERENCE:
============================

ServiceCategoryViewSet endpoints:
- GET    /api/services/categories/           - List categories
- POST   /api/services/categories/           - Create category (Admin only) 
- GET    /api/services/categories/{id}/      - Retrieve category
- PUT    /api/services/categories/{id}/      - Update category (Admin only)
- PATCH  /api/services/categories/{id}/      - Partial update (Admin only)
- DELETE /api/services/categories/{id}/      - Delete category (Admin only)
- GET    /api/services/categories/statistics/ - Get statistics (Admin only)

ServiceSubCategoryViewSet endpoints:
- GET    /api/services/subcategories/        - List subcategories
- POST   /api/services/subcategories/        - Create subcategory (Admin only)
- GET    /api/services/subcategories/{id}/   - Retrieve subcategory  
- PUT    /api/services/subcategories/{id}/   - Update subcategory (Admin only)
- PATCH  /api/services/subcategories/{id}/   - Partial update (Admin only)
- DELETE /api/services/subcategories/{id}/   - Delete subcategory (Admin only)

ServiceViewSet endpoints:
- GET    /api/services/services/             - List services
- POST   /api/services/services/             - Create service (Provider only)
- GET    /api/services/services/{id}/        - Retrieve service
- PUT    /api/services/services/{id}/        - Update service (Owner only)
- PATCH  /api/services/services/{id}/        - Partial update (Owner only)
- DELETE /api/services/services/{id}/        - Delete service (Owner only)
- GET    /api/services/services/nearby/      - Find nearby services
- GET    /api/services/services/admin/       - Admin view (Admin only)
- GET    /api/services/services/trending/    - Get trending services
- GET    /api/services/services/matching_requests/ - Get matching requests (Provider only)
- GET    /api/services/services/by_availability/ - Filter by availability
- GET    /api/services/services/{id}/matching_services/ - Find matching services
- POST   /api/services/services/{id}/fulfill_request/ - Fulfill request (Provider only)

ServiceRequestViewSet endpoints:
- GET    /api/services/requests/             - List service requests
- POST   /api/services/requests/             - Create request (Customer only)
- GET    /api/services/requests/{id}/        - Retrieve request
- PUT    /api/services/requests/{id}/        - Update request (Owner only)
- PATCH  /api/services/requests/{id}/        - Partial update (Owner only)
- DELETE /api/services/requests/{id}/        - Delete request (Owner only)
- GET    /api/services/requests/my_requests/ - Customer's own requests
- GET    /api/services/requests/admin/       - Admin view (Admin only)
- GET    /api/services/requests/{id}/recommended_providers/ - Get recommended providers
- POST   /api/services/requests/batch_expire/ - Expire old requests (Admin only)
- POST   /api/services/requests/{id}/cancel/ - Cancel request (Owner only)
"""

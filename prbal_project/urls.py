"""
URL configuration for prbal_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Import drf-spectacular schema
from .schema import urlpatterns as schema_urls

# Swagger/OpenAPI documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="Prbal API",
        default_version='v1',
        description="API for Prbal service marketplace",
        contact=openapi.Contact(email="contact@prbal.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Health check endpoint for monitoring and container orchestration
def health_check(request):
    return JsonResponse({"status": "healthy", "version": "1.0.0"})

# Database health check
def db_health_check(request):
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            one = cursor.fetchone()[0]
            if one == 1:
                return JsonResponse({"status": "database_connected"})
    except Exception as e:
        return JsonResponse({"status": "database_error", "message": str(e)}, status=500)
    return JsonResponse({"status": "database_error"}, status=500)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check endpoints
    path('api/v1/health/', health_check, name='health_check'),
    path('api/v1/health/db/', db_health_check, name='db_health_check'),
    
    # Prometheus metrics endpoints
    path('', include('django_prometheus.urls')),
    
    # API endpoints
    path('api/v1/', include('users.urls')),
    path('api/v1/products/', include('products.urls')),
    path('api/v1/bids/', include('bids.urls')),
    path('api/v1/bookings/', include('bookings.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('api/v1/messaging/', include('messagings.urls')),
    path('api/v1/notifications/', include('notifications.urls')),
    path('api/v1/ai-suggestions/', include('ai_suggestions.urls')),
    path('api/v1/reviews/', include('reviews.urls')),
    path('api/v1/services/', include('services.urls')),
    
    # Sync APIs for offline functionality
    path('api/v1/sync/', include('sync.urls')),
    
    # Integration APIs for external services
    path('api/v1/integrations/calendar/sync/', include('bookings.calendar_urls')),

    
    # Analytics & Admin APIs
    path('api/v1/analytics/', include('analytics.urls')),
    
    # Swagger documentation (legacy)
    path('api/v1/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/v1/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Add drf-spectacular schema URLs
urlpatterns += schema_urls

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, you would configure your web server (nginx, etc.) to serve these
    # This is a fallback for development/testing in non-DEBUG mode
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

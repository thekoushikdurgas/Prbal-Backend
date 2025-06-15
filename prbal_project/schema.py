"""
API schema configuration for drf-spectacular.
Provides OpenAPI 3.0 documentation for the Prbal API.
"""
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from django.urls import path

urlpatterns = [
    # API Schema
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Swagger UI
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # ReDoc UI (alternative API docs interface)
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

spectacular_settings = {
    'TITLE': 'Prbal API',
    'DESCRIPTION': 'Service marketplace API for connecting providers and customers',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
    },
    'TAGS': [
        {'name': 'Authentication', 'description': 'Auth endpoints'},
        {'name': 'Users', 'description': 'User management endpoints'},
        {'name': 'Services', 'description': 'Service listing and management'},
        {'name': 'Bids', 'description': 'Bid submission and management'},
        {'name': 'Bookings', 'description': 'Booking creation and management'},
        {'name': 'Payments', 'description': 'Payment processing endpoints'},
        {'name': 'Reviews', 'description': 'Service review endpoints'},
        {'name': 'Verification', 'description': 'User verification endpoints'},
        {'name': 'Messaging', 'description': 'Chat and messaging endpoints'},
        {'name': 'Notifications', 'description': 'Notification endpoints'},
        {'name': 'AI Suggestions', 'description': 'AI-powered service suggestions'},
        {'name': 'Products', 'description': 'Product listing and management'},
    ],
}

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageThreadViewSet, MessageViewSet, ThreadMessagesViewSet

# Router for the standard REST endpoints
router = DefaultRouter()
router.register(r'threads', MessageThreadViewSet, basename='message-thread')
router.register(r'messages', MessageViewSet, basename='message')

# Define the direct thread message URLs that match the requirements
urlpatterns = [
    # Include router URLs for the standard REST endpoints
    path('', include(router.urls)),
    
    # Custom URL pattern for thread messages that matches the required structure
    path('<uuid:thread_id>/', ThreadMessagesViewSet.as_view({'get': 'list', 'post': 'create'}), name='thread-messages'),
]

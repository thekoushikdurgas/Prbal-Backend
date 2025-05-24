from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import (
    views, booking_views, chat_views,
    notification_views, ai_views, payout_views
)

app_name = 'services'

router = DefaultRouter()
router.register(r'categories', views.ServiceCategoryViewSet, basename='category')
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'requests', views.ServiceRequestViewSet, basename='request')
router.register(r'bids', views.BidViewSet, basename='bid')
router.register(r'bookings', booking_views.BookingViewSet, basename='booking')
router.register(r'payments', views.PaymentViewSet, basename='payment')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'payouts', payout_views.PayoutViewSet, basename='payout')
router.register(r'notifications', notification_views.NotificationViewSet, basename='notification')
router.register(r'chats', chat_views.ChatViewSet, basename='chat')
router.register(r'ai', ai_views.AIRecommendationViewSet, basename='ai')

urlpatterns = [
    path('', include(router.urls)),
]

# Ensure views.py has:
# ServiceCategoryViewSet, ServiceViewSet, ServiceRequestViewSet, BidViewSet, BookingViewSet, ChatMessageViewSet 
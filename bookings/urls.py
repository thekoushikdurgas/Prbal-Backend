from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet
from .views import CalendarSyncView

router = DefaultRouter()
router.register(r'', BookingViewSet)

urlpatterns = [
    # POST endpoint for calendar sync
    path('', CalendarSyncView.as_view(), name='calendar-sync'),
    path('', include(router.urls)),
]

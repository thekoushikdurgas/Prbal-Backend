"""
URL configuration for calendar integration APIs.
"""
from django.urls import path
from .calendar_views import CalendarSyncView

urlpatterns = [
    # POST endpoint for calendar sync
    path('', CalendarSyncView.as_view(), name='calendar-sync'),
]

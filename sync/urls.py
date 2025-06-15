from django.urls import path
from .views import UserProfileSyncView, ServicesSyncView, SyncUploadView

urlpatterns = [
    # Download user profile for offline use
    path('profile/', UserProfileSyncView.as_view(), name='sync-profile'),
    
    # Download available services for offline browsing
    path('services/', ServicesSyncView.as_view(), name='sync-services'),
    
    # Upload offline changes to the backend
    path('upload/', SyncUploadView.as_view(), name='sync-upload'),
]

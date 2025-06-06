from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VerificationViewSet

router = DefaultRouter()
router.register(r'', VerificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

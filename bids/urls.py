from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BidViewSet

router = DefaultRouter()
router.register(r'', BidViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

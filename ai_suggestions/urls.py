from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'suggestions', views.AISuggestionViewSet)
router.register(r'feedback', views.AIFeedbackLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

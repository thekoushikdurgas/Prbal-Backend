from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView, UserLoginView,
    UserViewSet, CustomerProfileViewSet,
    ServiceProviderProfileViewSet, SkillViewSet,
    ProfileImageUploadView
)

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'customer-profiles', CustomerProfileViewSet)
router.register(r'provider-profiles', ServiceProviderProfileViewSet)
router.register(r'skills', SkillViewSet)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/image/', ProfileImageUploadView.as_view(), name='profile-image-upload'),
    path('', include(router.urls)),
] 
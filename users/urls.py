from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    # Generic user views
    UserProfileView,
    UserPublicProfileView,
    ProfileImageUploadView,
    UserProfileLikeView,
    UserProfilePassView,
    UserVerificationView,
    # Admin specific views
    AdminRegistrationView,
    # Search views
    UserSearchByPhoneView,
    UserSearchView,
    UserDeactivateView, # Added for account deactivation
    # Access token management
    UserAccessTokensView,
    UserAccessTokenRevokeView,
    UserAccessTokenRevokeAllView,
    # PIN Authentication views
    PinLoginView,
    PinRegistrationView,
    ChangePinView,
    ResetPinView,
    PinStatusView,
    # User type detection
    UserTypeView,
    UserTypeChangeView,
    VerificationViewSet,
    ProfilePictureUrlTestView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'verifications', VerificationViewSet, basename='verification')

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', PinLoginView.as_view(), name='pin-login'),
    path('auth/register/', PinRegistrationView.as_view(), name='pin-register'),
    path('auth/admin/register/', AdminRegistrationView.as_view(), name='admin-register'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # PIN management endpoints
    path('auth/pin/change/', ChangePinView.as_view(), name='pin-change'),
    path('auth/pin/reset/', ResetPinView.as_view(), name='pin-reset'),
    path('auth/pin/status/', PinStatusView.as_view(), name='pin-status'),
    
    # User type management endpoints
    path('auth/user-type/', UserTypeView.as_view(), name='user-type'),
    path('auth/user-type-change/', UserTypeChangeView.as_view(), name='user-type-change'),
    
    # Profile management endpoints
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'), # Added for account deactivation
    path('users/profile/image/', ProfileImageUploadView.as_view(), name='profile-image-upload'),
    path('users/<uuid:id>/', UserPublicProfileView.as_view(), name='user-public-profile'),
    path('users/<uuid:id>/like/', UserProfileLikeView.as_view(), name='user-like'),
    path('users/<uuid:id>/pass/', UserProfilePassView.as_view(), name='user-pass'),
    
    # Search endpoints
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('users/search/phone/', UserSearchByPhoneView.as_view(), name='user-search-phone'),
    
    # Verification endpoints
    path('users/verify/', UserVerificationView.as_view(), name='user-verification'),
    
    # Token management endpoints
    path('users/me/tokens/', UserAccessTokensView.as_view(), name='user-tokens'),
    path('users/me/tokens/<uuid:token_id>/revoke/', UserAccessTokenRevokeView.as_view(), name='user-token-revoke'),
    path('users/me/tokens/revoke_all/', UserAccessTokenRevokeAllView.as_view(), name='user-tokens-revoke-all'),
    
    # Include ViewSet URLs
    path('users/', include(router.urls)),
]

# Note: All login endpoints removed as password functionality is being removed:
# - path('auth/login/', UserLoginView.as_view(), name='user-login'),
# - path('auth/customer/login/', CustomerLoginView.as_view(), name='customer-login'),
# - path('auth/provider/login/', ProviderLoginView.as_view(), name='provider-login'),
# - path('auth/admin/login/', AdminLoginView.as_view(), name='admin-login'),
# - path('users/me/change-password/', ChangePasswordView.as_view(), name='user-change-password'),

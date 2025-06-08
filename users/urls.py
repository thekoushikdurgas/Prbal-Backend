from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    # Generic user views
    UserRegistrationView,
    UserProfileView,
    UserPublicProfileView,
    UserAvatarUploadView,
    ProfileImageUploadView,
    UserProfileLikeView,
    UserProfilePassView,
    UserVerificationView,
    # Customer specific views
    CustomerRegistrationView,
    CustomerProfileView,
    # Provider specific views
    ProviderRegistrationView,
    ProviderProfileView,
    # Admin specific views
    AdminRegistrationView,
    AdminProfileView,
    # Search views
    UserSearchByPhoneView,
    UserSearchView,
    UserDeactivateView, # Added for account deactivation
    # Access token management
    UserAccessTokensView,
    UserAccessTokenRevokeView,
    # PIN Authentication views
    PinLoginView,
    PinRegistrationView,
    CustomerPinRegistrationView,
    ProviderPinRegistrationView,
    ChangePinView,
    ResetPinView,
    PinStatusView
)

urlpatterns = [
    # PIN-based authentication endpoints
    path('auth/pin/login/', PinLoginView.as_view(), name='pin-login'),
    path('auth/pin/register/', PinRegistrationView.as_view(), name='pin-register'),
    path('auth/pin/customer/register/', CustomerPinRegistrationView.as_view(), name='customer-pin-register'),
    path('auth/pin/provider/register/', ProviderPinRegistrationView.as_view(), name='provider-pin-register'),
    path('auth/pin/change/', ChangePinView.as_view(), name='change-pin'),
    path('auth/pin/reset/', ResetPinView.as_view(), name='reset-pin'),
    path('auth/pin/status/', PinStatusView.as_view(), name='pin-status'),
    
    # Generic authentication endpoints (registration only - no login/password functionality)
    path('auth/register/', UserRegistrationView.as_view(), name='user-register'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Customer-specific endpoints
    path('auth/customer/register/', CustomerRegistrationView.as_view(), name='customer-register'),
    path('users/customer/me/', CustomerProfileView.as_view(), name='customer-profile'),
    
    # Provider-specific endpoints
    path('auth/provider/register/', ProviderRegistrationView.as_view(), name='provider-register'),
    path('users/provider/me/', ProviderProfileView.as_view(), name='provider-profile'),
    
    # Admin-specific endpoints
    path('auth/admin/register/', AdminRegistrationView.as_view(), name='admin-register'),
    path('users/admin/me/', AdminProfileView.as_view(), name='admin-profile'),
    
    # Generic user profile endpoints
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/me/avatar/', UserAvatarUploadView.as_view(), name='user-avatar-upload'),
    path('users/me/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'), # Added for account deactivation
    path('users/profile/image/', ProfileImageUploadView.as_view(), name='profile-image-upload'),
    path('users/<uuid:id>/', UserPublicProfileView.as_view(), name='user-public-profile'),
    path('users/<uuid:id>/like/', UserProfileLikeView.as_view(), name='user-profile-like'),
    path('users/<uuid:id>/pass/', UserProfilePassView.as_view(), name='user-profile-pass'),
    
    # Verification endpoints
    path('users/verify/', UserVerificationView.as_view(), name='user-verify'),
    
    # Access token management endpoints
    path('users/me/tokens/', UserAccessTokensView.as_view(), name='user-access-tokens'),
    path('users/me/tokens/<uuid:token_id>/revoke/', UserAccessTokenRevokeView.as_view(), name='user-token-revoke'),
    
    # Search endpoints
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('users/search/phone/', UserSearchByPhoneView.as_view(), name='user-search-by-phone'),
]

# Note: All login endpoints removed as password functionality is being removed:
# - path('auth/login/', UserLoginView.as_view(), name='user-login'),
# - path('auth/logout/', UserLogoutView.as_view(), name='user-logout'),
# - path('auth/customer/login/', CustomerLoginView.as_view(), name='customer-login'),
# - path('auth/provider/login/', ProviderLoginView.as_view(), name='provider-login'),
# - path('auth/admin/login/', AdminLoginView.as_view(), name='admin-login'),
# - path('users/me/change-password/', ChangePasswordView.as_view(), name='user-change-password'),

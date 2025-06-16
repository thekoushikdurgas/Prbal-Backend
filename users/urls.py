from django.urls import path
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
    VerificationViewSet
)

urlpatterns = [
    # PIN-based authentication endpoints
    path('auth/login/', PinLoginView.as_view(), name='pin-login'),
    path('auth/register/', PinRegistrationView.as_view(), name='pin-register'),
    path('auth/pin/change/', ChangePinView.as_view(), name='change-pin'),
    path('auth/pin/reset/', ResetPinView.as_view(), name='reset-pin'),
    path('auth/pin/status/', PinStatusView.as_view(), name='pin-status'),
    
    # User type detection endpoint
    path('auth/user-type/', UserTypeView.as_view(), name='user-type'),
    path('auth/user-type-change/', UserTypeChangeView.as_view(), name='user-type-change'),
    
    # Admin-specific endpoints
    path('auth/admin/register/', AdminRegistrationView.as_view(), name='admin-register'),
    
    # Generic user profile endpoints
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path('users/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'), # Added for account deactivation
    path('users/profile/image/', ProfileImageUploadView.as_view(), name='profile-image-upload'),
    path('users/<uuid:id>/', UserPublicProfileView.as_view(), name='user-public-profile'),
    path('users/<uuid:id>/like/', UserProfileLikeView.as_view(), name='user-profile-like'),
    path('users/<uuid:id>/pass/', UserProfilePassView.as_view(), name='user-profile-pass'),
    
    # Verification endpoints
    path('users/verify/', UserVerificationView.as_view(), name='user-verify'),
    path('users/verifications/', VerificationViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-verifications'),
    path('users/verifications/<int:pk>/', VerificationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='user-verification-detail'),
    path('users/verifications/<int:pk>/cancel/', VerificationViewSet.as_view({'post': 'cancel'}), name='user-verification-cancel'),
    path('users/verifications/<int:pk>/mark_in_progress/', VerificationViewSet.as_view({'post': 'mark_in_progress'}), name='user-verification-mark-in-progress'),
    path('users/verifications/<int:pk>/mark_verified/', VerificationViewSet.as_view({'post': 'mark_verified'}), name='user-verification-mark-verified'),
    path('users/verifications/<int:pk>/mark_rejected/', VerificationViewSet.as_view({'post': 'mark_rejected'}), name='user-verification-mark-rejected'),
    path('users/verifications/status_summary/', VerificationViewSet.as_view({'get': 'status_summary'}), name='user-verifications-status-summary'),
    
    # Access token management endpoints
    path('users/me/tokens/', UserAccessTokensView.as_view(), name='user-access-tokens'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/me/tokens/<uuid:token_id>/revoke/', UserAccessTokenRevokeView.as_view(), name='user-token-revoke'),
    path('users/me/tokens/revoke_all/', UserAccessTokenRevokeAllView.as_view(), name='user-tokens-revoke-all'),
    
    # Search endpoints
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    path('users/search/phone/', UserSearchByPhoneView.as_view(), name='user-search-by-phone'),
]

# Note: All login endpoints removed as password functionality is being removed:
# - path('auth/login/', UserLoginView.as_view(), name='user-login'),
# - path('auth/customer/login/', CustomerLoginView.as_view(), name='customer-login'),
# - path('auth/provider/login/', ProviderLoginView.as_view(), name='provider-login'),
# - path('auth/admin/login/', AdminLoginView.as_view(), name='admin-login'),
# - path('users/me/change-password/', ChangePasswordView.as_view(), name='user-change-password'),

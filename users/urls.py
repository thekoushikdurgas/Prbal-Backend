"""
🔗 Users App URL Configuration

This module defines all URL patterns for the Users app, implementing a comprehensive
user management system with PIN-based authentication, profile management, verification
system, and role-based access control.

🏗️ Architecture Overview:
- PIN-based Authentication (no passwords)
- Multi-user Types: Customer, Provider, Admin
- JWT Token Management with device tracking
- Comprehensive verification system
- Advanced search capabilities
- File upload support (URLs, base64, local files)

📚 URL Pattern Categories:
1. Authentication & Registration (auth/*)
2. User Profile Management (users/*)
3. Verification System (users/verifications/*)
4. Token Management (users/me/tokens/*)
5. Search & Discovery (users/search/*)

🔐 Security Features:
- Role-based permissions
- PIN lockout mechanism (5 failed attempts = 30min lockout)
- Device tracking and session management
- Secure file upload handling

📊 Response Format:
All endpoints use standardized JSON responses:
{
    "message": "Human-readable message",
    "data": "Response data",
    "time": "ISO timestamp",
    "statusCode": "HTTP status code"
}
"""

import logging
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

# Configure debug logging for URL resolution
logger = logging.getLogger(__name__)
logger.info("🔗 Loading Users App URL Configuration...")

# Import all view classes with organized grouping
from .views import (
    # 👤 Generic user profile views
    UserProfileView,           # GET/PUT/PATCH /users/me/ - Own profile management
    UserPublicProfileView,     # GET /users/<uuid>/ - Public profile viewing
    ProfileImageUploadView,    # POST /users/profile/image/ - Profile image upload
    UserProfileLikeView,       # POST /users/<uuid>/like/ - Like user profile
    UserProfilePassView,       # POST /users/<uuid>/pass/ - Pass on user profile
    UserVerificationView,      # POST /users/verify/ - Submit verification request
    
    # 👑 Admin specific views
    AdminRegistrationView,     # POST /auth/admin/register/ - Admin registration
    
    # 🔍 Search and discovery views
    UserSearchByPhoneView,     # GET/POST /users/search/phone/ - Phone number search (PUBLIC)
    UserSearchView,           # GET/POST /users/search/ - Advanced search (AUTHENTICATED)
    UserDeactivateView,       # POST /users/deactivate/ - Account deactivation
    
    # 🎫 Access token management views
    UserAccessTokensView,        # GET /users/me/tokens/ - List user's tokens
    UserAccessTokenRevokeView,   # POST /users/me/tokens/<uuid>/revoke/ - Revoke single token
    UserAccessTokenRevokeAllView, # POST /users/me/tokens/revoke_all/ - Revoke all tokens
    
    # 🔐 PIN Authentication views (Core authentication system)
    PinLoginView,             # POST /auth/login/ - PIN-based login (ALL USER TYPES)
    PinRegistrationView,      # POST /auth/register/ - PIN-based registration
    ChangePinView,           # POST /auth/pin/change/ - Change existing PIN
    ResetPinView,            # POST /auth/pin/reset/ - Reset PIN via phone verification
    PinStatusView,           # GET /auth/pin/status/ - Check PIN lock status
    
    # 🏷️ User type management views
    UserTypeView,            # GET /auth/user-type/ - Detect user type from token
    UserTypeChangeView,      # GET/POST /auth/user-type-change/ - Change user type
    
    # ✅ Verification system ViewSet
    VerificationViewSet      # ViewSet for comprehensive verification management
)

# Debug: Log all imported views
logger.debug("📦 Imported Views:")
view_classes = [
    UserProfileView, UserPublicProfileView, ProfileImageUploadView,
    UserProfileLikeView, UserProfilePassView, UserVerificationView,
    AdminRegistrationView, UserSearchByPhoneView, UserSearchView,
    UserDeactivateView, UserAccessTokensView, UserAccessTokenRevokeView,
    UserAccessTokenRevokeAllView, PinLoginView, PinRegistrationView,
    ChangePinView, ResetPinView, PinStatusView, UserTypeView,
    UserTypeChangeView, VerificationViewSet
]

for view_class in view_classes:
    logger.debug(f"   ✅ {view_class.__name__}")

# 🗺️ URL Patterns Definition
# Each pattern is organized by functional category with detailed comments

print("🚀 Configuring Users App URL Patterns...")
print("=" * 60)

urlpatterns = [
    # ============================================================================
    # 🔐 AUTHENTICATION & REGISTRATION ENDPOINTS
    # ============================================================================
    # These endpoints handle user authentication, registration, and PIN management
    
    # Core Authentication
    path('auth/login/', PinLoginView.as_view(), name='pin-login'),
    # 🎯 PIN Login: Authenticates ALL user types (customer, provider, admin)
    # - Method: POST
    # - Permission: AllowAny (public)
    # - Input: {"phone_number": "+1234567890", "pin": "1234"}
    # - Security: PIN lockout after 5 failed attempts (30min timeout)
    # - Returns: User profile + JWT tokens
    
    path('auth/register/', PinRegistrationView.as_view(), name='pin-register'),
    # 🎯 PIN Registration: Create new user account with PIN
    # - Method: POST  
    # - Permission: AllowAny (public)
    # - Input: {"username", "email", "phone_number", "pin", "confirm_pin"}
    # - Validation: PIN strength checking, phone uniqueness
    # - Returns: User profile + JWT tokens
    
    # PIN Management
    path('auth/pin/change/', ChangePinView.as_view(), name='change-pin'),
    # 🎯 Change PIN: Update existing PIN (requires current PIN)
    # - Method: POST
    # - Permission: IsAuthenticated
    # - Input: {"current_pin", "new_pin", "confirm_new_pin"}
    # - Security: Validates current PIN before allowing change
    
    path('auth/pin/reset/', ResetPinView.as_view(), name='reset-pin'),
    # 🎯 Reset PIN: Reset PIN via phone verification
    # - Method: POST
    # - Permission: AllowAny (public)
    # - Input: {"phone_number", "new_pin", "confirm_new_pin"}
    # - TODO: Add phone verification code requirement
    
    path('auth/pin/status/', PinStatusView.as_view(), name='pin-status'),
    # 🎯 PIN Status: Check PIN lock status and failed attempts
    # - Method: GET
    # - Permission: IsAuthenticated
    # - Returns: Lock status, failed attempts, remaining lock time
    
    # User Type Management
    path('auth/user-type/', UserTypeView.as_view(), name='user-type'),
    # 🎯 User Type Detection: Identify user type from JWT token
    # - Method: GET
    # - Permission: IsAuthenticated
    # - Returns: User type info (customer/provider/admin)
    
    path('auth/user-type-change/', UserTypeChangeView.as_view(), name='user-type-change'),
    # 🎯 User Type Change: Change between customer/provider types
    # - Methods: GET (info), POST (change)
    # - Permission: IsAuthenticated
    # - Restrictions: Admins cannot change type, phone required for provider
    
    # Admin Registration
    path('auth/admin/register/', AdminRegistrationView.as_view(), name='admin-register'),
    # 🎯 Admin Registration: Create admin account (requires secret code)
    # - Method: POST
    # - Permission: AllowAny (but requires admin_code validation)
    # - Input: Standard registration + {"admin_code": "secret"}
    # - Sets: is_staff=True, user_type='admin'
    
    # ============================================================================
    # 👤 USER PROFILE MANAGEMENT ENDPOINTS  
    # ============================================================================
    # These endpoints handle user profile operations and social features
    
    # Own Profile Management
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    # 🎯 Own Profile: Get/Update authenticated user's profile
    # - Methods: GET (retrieve), PUT (full update), PATCH (partial update)
    # - Permission: IsAuthenticated
    # - Features: Enhanced file upload (URLs, base64, local files)
    # - Returns: Complete user profile with all fields
    
    path('users/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'),
    # 🎯 Account Deactivation: Deactivate user's own account
    # - Method: POST
    # - Permission: IsAuthenticated
    # - Action: Sets is_active=False (reversible by admin)
    # - Security: Cannot deactivate already inactive account
    
    # Profile Image Management
    path('users/profile/image/', ProfileImageUploadView.as_view(), name='profile-image-upload'),
    # 🎯 Profile Image Upload: Upload/update profile picture
    # - Method: POST
    # - Permission: IsAuthenticated
    # - Supports: File upload, URL, base64 data
    # - Features: Automatic image optimization and resizing
    # - Max Size: 5MB, formats: JPEG, PNG, GIF, WebP, BMP
    
    # Public Profile Access
    path('users/<uuid:id>/', UserPublicProfileView.as_view(), name='user-public-profile'),
    # 🎯 Public Profile View: View any user's public profile
    # - Method: GET
    # - Permission: AllowAny (public)
    # - Returns: Limited public fields only (no sensitive data)
    # - UUID Parameter: User's unique identifier
    
    # Social Features
    path('users/<uuid:id>/like/', UserProfileLikeView.as_view(), name='user-profile-like'),
    # 🎯 Like Profile: Like/match with another user
    # - Method: POST
    # - Permission: IsAuthenticated
    # - Restriction: Cannot like own profile
    # - Creates: Like relationship record
    
    path('users/<uuid:id>/pass/', UserProfilePassView.as_view(), name='user-profile-pass'),
    # 🎯 Pass Profile: Pass on/reject user profile
    # - Method: POST
    # - Permission: IsAuthenticated
    # - Action: Records preference for matching algorithm
    
    # ============================================================================
    # ✅ VERIFICATION SYSTEM ENDPOINTS
    # ============================================================================
    # Comprehensive document verification system with admin workflow
    
    # Simple Verification Submission
    path('users/verify/', UserVerificationView.as_view(), name='user-verify'),
    # 🎯 Simple Verification: Quick verification submission
    # - Method: POST
    # - Permission: IsAuthenticated
    # - Input: document_link, document_type, verification_type
    # - Features: URL/base64 document processing
    # - Duplicate Check: Prevents multiple pending verifications
    
    # ViewSet-based Verification Management
    path('users/verifications/', VerificationViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-verifications'),
    # 🎯 Verification List/Create: List verifications or create new
    # - Methods: GET (list), POST (create)
    # - Permission: IsAuthenticated
    # - Filtering: Users see only their verifications, admins see all
    # - Features: Enhanced file processing, multiple input methods
    
    path('users/verifications/<int:pk>/', VerificationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='user-verification-detail'),
    # 🎯 Verification Detail: Full CRUD operations on verification
    # - Methods: GET, PUT, PATCH, DELETE
    # - Permission: Owner or Admin
    # - PK Type: Integer (verification ID)
    
    # Admin Verification Actions
    path('users/verifications/<int:pk>/cancel/', VerificationViewSet.as_view({'post': 'cancel'}), name='user-verification-cancel'),
    # 🎯 Cancel Verification: User cancels their pending verification
    # - Method: POST
    # - Permission: IsVerificationOwner
    # - Restriction: Only pending verifications can be cancelled
    
    path('users/verifications/<int:pk>/mark_in_progress/', VerificationViewSet.as_view({'post': 'mark_in_progress'}), name='user-verification-mark-in-progress'),
    # 🎯 Mark In Progress: Admin marks verification as being reviewed
    # - Method: POST
    # - Permission: IsVerificationAdmin
    # - Input: Optional verification_notes
    
    path('users/verifications/<int:pk>/mark_verified/', VerificationViewSet.as_view({'post': 'mark_verified'}), name='user-verification-mark-verified'),
    # 🎯 Mark Verified: Admin approves verification
    # - Method: POST
    # - Permission: IsVerificationAdmin
    # - Action: Sets user.is_verified=True for identity verifications
    # - Sets: verified_at, expires_at (365 days default)
    
    path('users/verifications/<int:pk>/mark_rejected/', VerificationViewSet.as_view({'post': 'mark_rejected'}), name='user-verification-mark-rejected'),
    # 🎯 Mark Rejected: Admin rejects verification with reason
    # - Method: POST
    # - Permission: IsVerificationAdmin
    # - Required: rejection_reason
    # - Optional: verification_notes
    
    path('users/verifications/status_summary/', VerificationViewSet.as_view({'get': 'status_summary'}), name='user-verifications-status-summary'),
    # 🎯 Status Summary: Admin dashboard statistics
    # - Method: GET
    # - Permission: IsVerificationAdmin (staff only)
    # - Returns: Counts by status and verification type
    
    # ============================================================================
    # 🎫 ACCESS TOKEN MANAGEMENT ENDPOINTS
    # ============================================================================
    # JWT token lifecycle management with device tracking
    
    path('users/me/tokens/', UserAccessTokensView.as_view(), name='user-access-tokens'),
    # 🎯 List Tokens: View all user's active/inactive tokens
    # - Method: GET
    # - Permission: IsAuthenticated
    # - Query Params: ?active_only=true (filter active tokens)
    # - Returns: Token list with device info, creation time, last used
    
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    # 🎯 Refresh Token: Get new access token using refresh token
    # - Method: POST
    # - Permission: None (handled by SimpleJWT)
    # - Input: {"refresh": "refresh_token_here"}
    # - Returns: New access token
    # - Note: Uses DRF SimpleJWT standard implementation
    
    path('users/me/tokens/<uuid:token_id>/revoke/', UserAccessTokenRevokeView.as_view(), name='user-token-revoke'),
    # 🎯 Revoke Single Token: Revoke specific access token
    # - Method: POST
    # - Permission: IsAuthenticated
    # - Action: Sets token.is_active=False
    # - Security: Users can only revoke their own tokens
    
    path('users/me/tokens/revoke_all/', UserAccessTokenRevokeAllView.as_view(), name='user-tokens-revoke-all'),
    # 🎯 Revoke All Tokens: Log out from all devices
    # - Method: POST
    # - Permission: IsAuthenticated
    # - Action: Deactivates all user's active tokens
    # - Use Case: Security breach, stolen device, etc.
    
    # ============================================================================
    # 🔍 SEARCH & DISCOVERY ENDPOINTS
    # ============================================================================
    # User search functionality with role-based filtering
    
    path('users/search/', UserSearchView.as_view(), name='user-search'),
    # 🎯 Advanced Search: Role-based user search with filtering
    # - Methods: GET (backward compatibility), POST (advanced)
    # - Permission: IsAuthenticated
    # - Role Filtering:
    #   * Customers can search Providers
    #   * Providers can search Customers  
    #   * Admins can search both (+ other admins if requested)
    # - Features: Pagination, sorting, multi-field search
    # - Filters: user_type, location, rating, skills, verification status
    
    path('users/search/phone/', UserSearchByPhoneView.as_view(), name='user-search-by-phone'),
    # 🎯 Phone Search: Public phone number search (NO AUTH REQUIRED)
    # - Methods: GET (?phone_number=X), POST ({"phone_number": "X"})
    # - Permission: AllowAny (public endpoint)
    # - Search Strategy: Exact match first, then partial match
    # - Returns: User-type-specific serialized data
    # - Security: Returns only public profile fields
    # - Use Case: Contact discovery, user lookup
]

# Debug: Log URL pattern loading completion
logger.info("✅ Users App URLs loaded successfully!")
logger.info(f"📊 Total URL patterns: {len(urlpatterns)}")

# Debug: Print URL pattern summary by category
print("\n📋 URL Pattern Summary:")
print("-" * 60)

# Count patterns by category
auth_patterns = [p for p in urlpatterns if str(p.pattern).startswith('auth/')]
user_patterns = [p for p in urlpatterns if str(p.pattern).startswith('users/') and 'verifications' not in str(p.pattern) and 'tokens' not in str(p.pattern)]
verification_patterns = [p for p in urlpatterns if 'verifications' in str(p.pattern)]
token_patterns = [p for p in urlpatterns if 'tokens' in str(p.pattern) or 'token' in str(p.pattern)]

print(f"🔐 Authentication & Registration: {len(auth_patterns)} endpoints")
print(f"👤 User Profile Management: {len(user_patterns)} endpoints") 
print(f"✅ Verification System: {len(verification_patterns)} endpoints")
print(f"🎫 Token Management: {len(token_patterns)} endpoints")
print(f"📊 Total: {len(urlpatterns)} endpoints")

# Debug: Log pattern names for debugging
logger.debug("🏷️ URL Pattern Names:")
for pattern in urlpatterns:
    logger.debug(f"   📍 {pattern.name}: {pattern.pattern}")

print("\n🎯 Key Features:")
print("   ✅ PIN-based Authentication (no passwords)")
print("   ✅ Multi-user Types (Customer, Provider, Admin)")
print("   ✅ JWT Token Management with Device Tracking")
print("   ✅ Comprehensive Verification System")
print("   ✅ Advanced Search & Discovery")
print("   ✅ File Upload Support (URLs, Base64, Local)")
print("   ✅ Role-based Access Control")
print("   ✅ Standardized API Responses")

# ============================================================================
# 📝 REMOVED ENDPOINTS (Legacy Password System)
# ============================================================================
# The following endpoints were removed during password → PIN migration:
#
# - path('auth/login/', UserLoginView.as_view(), name='user-login')
# - path('auth/customer/login/', CustomerLoginView.as_view(), name='customer-login')  
# - path('auth/provider/login/', ProviderLoginView.as_view(), name='provider-login')
# - path('auth/admin/login/', AdminLoginView.as_view(), name='admin-login')
# - path('users/me/change-password/', ChangePasswordView.as_view(), name='user-change-password')
#
# 🔄 Migration Notes:
# - All authentication now uses PIN + phone number
# - JWT tokens provide session management
# - PIN system includes lockout protection (5 attempts = 30min timeout)
# - Users can change PINs via /auth/pin/change/
# - PIN reset available via /auth/pin/reset/ (phone verification)
# ============================================================================

logger.info("🔗 Users App URL configuration complete!")
print("=" * 60)
print("🚀 Ready to handle user management requests!")

"""
ENDPOINT MAPPING REFERENCE:
============================

🔐 AUTHENTICATION & REGISTRATION ENDPOINTS:
- POST   /auth/login/                           - PIN-based login (All user types)
- POST   /auth/register/                        - PIN-based registration
- POST   /auth/pin/change/                      - Change existing PIN (Auth required)
- POST   /auth/pin/reset/                       - Reset PIN via phone verification
- GET    /auth/pin/status/                      - Check PIN lock status (Auth required)
- GET    /auth/user-type/                       - Detect user type from token (Auth required)
- GET    /auth/user-type-change/                - Get user type change info (Auth required)
- POST   /auth/user-type-change/                - Change user type (Auth required)
- POST   /auth/admin/register/                  - Admin registration (requires secret code)

👤 USER PROFILE MANAGEMENT ENDPOINTS:
- GET    /users/me/                             - Get own profile (Auth required)
- PUT    /users/me/                             - Update full profile (Auth required)
- PATCH  /users/me/                             - Partial profile update (Auth required)
- POST   /users/deactivate/                     - Deactivate own account (Auth required)
- POST   /users/profile/image/                  - Upload/update profile image (Auth required)
- GET    /users/<uuid:id>/                      - View public user profile (Public)
- POST   /users/<uuid:id>/like/                 - Like user profile (Auth required)
- POST   /users/<uuid:id>/pass/                 - Pass on user profile (Auth required)

✅ VERIFICATION SYSTEM ENDPOINTS:
- POST   /users/verify/                         - Submit verification request (Auth required)
- GET    /users/verifications/                  - List user verifications (Auth required)
- POST   /users/verifications/                  - Create new verification (Auth required)
- GET    /users/verifications/<int:pk>/         - Get verification details (Auth required)
- PUT    /users/verifications/<int:pk>/         - Update verification (Owner/Admin only)
- PATCH  /users/verifications/<int:pk>/         - Partial update verification (Owner/Admin only)
- DELETE /users/verifications/<int:pk>/         - Delete verification (Owner/Admin only)
- POST   /users/verifications/<int:pk>/cancel/  - Cancel verification (Owner only)
- POST   /users/verifications/<int:pk>/mark_in_progress/   - Mark as in progress (Admin only)
- POST   /users/verifications/<int:pk>/mark_verified/      - Mark as verified (Admin only)
- POST   /users/verifications/<int:pk>/mark_rejected/      - Mark as rejected (Admin only)
- GET    /users/verifications/status_summary/   - Get verification statistics (Admin only)

🎫 ACCESS TOKEN MANAGEMENT ENDPOINTS:
- GET    /users/me/tokens/                      - List user's tokens (Auth required)
- POST   /auth/token/refresh/                   - Refresh access token (Refresh token required)
- POST   /users/me/tokens/<uuid:token_id>/revoke/  - Revoke single token (Auth required)
- POST   /users/me/tokens/revoke_all/           - Revoke all user tokens (Auth required)

🔍 SEARCH & DISCOVERY ENDPOINTS:
- GET    /users/search/                         - Advanced user search (Auth required)
- POST   /users/search/                         - Advanced search with filters (Auth required)
- GET    /users/search/phone/                   - Search by phone number (Public)
- POST   /users/search/phone/                   - Search by phone number (Public)

📊 PERMISSION LEVELS:
- Public: No authentication required
- Auth required: Valid JWT token in Authorization header
- Owner only: User can only access their own resources
- Admin only: Staff/admin permissions required
- Owner/Admin: Either resource owner or admin can access

🔐 SECURITY FEATURES:
- PIN lockout: 5 failed attempts = 30-minute lockout
- Device tracking: All tokens tracked with device info
- Role-based access: Customers ↔ Providers ↔ Admins
- File validation: Secure upload with type/size limits
- Rate limiting: Ready for throttling implementation

🎯 AUTHENTICATION FLOW:
1. Register: POST /auth/register/ → Get tokens
2. Login: POST /auth/login/ → Get tokens  
3. Use: Include "Authorization: Bearer <access_token>" in requests
4. Refresh: POST /auth/token/refresh/ when access token expires
5. Logout: POST /users/me/tokens/revoke_all/ to revoke all sessions

📱 SUPPORTED INPUT FORMATS:
- Profile Images: File upload, URL, Base64 data
- Verification Docs: File upload, URL, Base64 data, Local paths
- Phone Numbers: International format (+1234567890)
- PINs: 4-digit numeric codes (1234)
- User Types: customer, provider, admin

🌐 RESPONSE FORMAT (All endpoints):
{
    "message": "Human-readable message",
    "data": "Response data (object/array/null)",
    "time": "ISO 8601 timestamp",
    "statusCode": "HTTP status code",
    "errors": "Validation errors (if applicable)"
}

📋 ENDPOINT CATEGORIES SUMMARY:
- 🔐 Authentication & Registration: 9 endpoints
- 👤 User Profile Management: 8 endpoints
- ✅ Verification System: 12 endpoints
- 🎫 Token Management: 4 endpoints
- 🔍 Search & Discovery: 4 endpoints
- 📊 Total: 37 endpoint patterns

🚀 READY FOR PRODUCTION USE!
"""

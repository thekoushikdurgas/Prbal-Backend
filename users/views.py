from rest_framework import status, generics, permissions, parsers, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import User, AccessToken # Assuming User is in users.models, if not, adjust
# Assuming Like model is in the same app's models.py. Adjust if it's elsewhere.
# from .models import Like # Or from another_app.models import Like
from django.db import transaction
from django.db.models import Q
from .tokens import CustomRefreshToken
from .permissions import IsCustomer, IsServiceProvider, IsAdmin

import logging
from django.db import IntegrityError, DatabaseError

logger = logging.getLogger(__name__)

from .serializers import (
    UserRegistrationSerializer,
    CustomerRegistrationSerializer,
    ProviderRegistrationSerializer,
    AdminRegistrationSerializer,
    UserProfileSerializer,
    PublicUserProfileSerializer,
    CustomerSearchResultSerializer,
    ProviderSearchResultSerializer,
    AdminSearchResultSerializer,
    AccessTokenSerializer,
    PinLoginSerializer,
    PinRegistrationSerializer,
    ChangePinSerializer,
    ResetPinSerializer,
    PinStatusSerializer,
    UserTypeSerializer,
    UserTypeChangeSerializer,
    UserTypeChangeInfoSerializer
)

User = get_user_model()


class UserAccessTokensView(generics.ListAPIView):
    """View for listing a user's access tokens"""
    serializer_class = AccessTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only return tokens for the currently authenticated user
        return AccessToken.objects.filter(user=self.request.user)
        
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Allow filtering by active status
        active_only = request.query_params.get('active_only', 'false').lower() == 'true'
        if active_only:
            queryset = queryset.filter(is_active=True)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })


class UserAccessTokenRevokeView(APIView):
    """View for revoking a specific access token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, token_id, *args, **kwargs):
        try:
            # Find the token and ensure it belongs to the current user
            token = get_object_or_404(AccessToken, id=token_id, user=request.user)
            
            # Mark as inactive
            token.is_active = False
            token.save(update_fields=['is_active'])
            
            return Response({
                'message': 'Token revoked successfully',
                'token_id': token_id
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error revoking token {token_id} for user {request.user.id}: {e}", exc_info=True)
            return Response({"detail": "An error occurred while revoking the token."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserAccessTokenRevokeAllView(APIView):
    """View for revoking all active access tokens for the authenticated user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            # Get all active tokens for the current user
            active_tokens = AccessToken.objects.filter(user=request.user, is_active=True)
            tokens_count = active_tokens.count()
            
            if tokens_count == 0:
                return Response({
                    'message': 'No active tokens to revoke',
                    'revoked_count': 0
                }, status=status.HTTP_200_OK)
            
            # Mark all active tokens as inactive
            active_tokens.update(is_active=False)
            
            logger.info(f"User {request.user.id} ({request.user.username}) revoked all {tokens_count} active tokens")
            
            return Response({
                'message': 'All active tokens revoked successfully',
                'revoked_count': tokens_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error revoking all tokens for user {request.user.id}: {e}", exc_info=True)
            return Response({"detail": "An error occurred while revoking all tokens."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Note: UserLogoutView removed as part of password removal - 
# Alternative token management should be implemented if needed


class UserDeactivateView(APIView):
    """
    Allows the currently authenticated user to deactivate their own account.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_active:
            return Response({"message": "Account is already deactivated."}, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_active = False
        try:
            user.save(update_fields=['is_active'])
            # Optionally, you might want to log the user out by invalidating tokens here
            # For example, if using SimpleJWT, blacklist the refresh token
            # from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            # try:
            #     # Assuming refresh token is sent in request body or handled elsewhere
            #     # This part is conceptual and needs actual refresh token handling
            #     refresh_token = request.data.get("refresh") # Or however you get it
            #     if refresh_token:
            #         token = RefreshToken(refresh_token)
            #         token.blacklist()
            # except Exception as e:
            #     logger.warning(f"Could not blacklist token for user {user.id} during deactivation: {e}")
            #     pass # Non-critical, proceed with deactivation message

            logger.info(f"User {user.id} ({user.username}) deactivated their account.")
            return Response({"message": "Account deactivated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error deactivating account for user {user.id}: {e}", exc_info=True)
            # Re-activate user if save failed to maintain consistent state, though unlikely with just one field.
            # user.is_active = True # This might be too aggressive or cause other issues.
            return Response({"detail": "An error occurred while deactivating your account. Please try again."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BaseRegistrationView(generics.CreateAPIView):
    """Base view for handling user registration"""
    permission_classes = [permissions.AllowAny]
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
            except IntegrityError as e:
                logger.warning(f"Registration IntegrityError for {request.data.get('email', 'N/A')}: {e}")
                error_detail = {}
                err_str = str(e).lower()
                if 'username' in err_str:
                    error_detail['username'] = ['A user with that username already exists.']
                elif 'email' in err_str:
                    error_detail['email'] = ['A user with that email address already exists.']
                elif 'phone_number' in err_str and request.data.get('phone_number'):
                     error_detail['phone_number'] = ['A user with that phone number already exists.']
                else:
                    error_detail['detail'] = ['An account with some of your provided information already exists.']
                return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)
            except DatabaseError as e:
                logger.error(f"Registration DatabaseError for {request.data.get('email', 'N/A')}: {e}", exc_info=True)
                return Response({"detail": "A database error occurred during registration. Please try again later."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                logger.error(f"Unexpected error during user save for {request.data.get('email', 'N/A')}: {e}", exc_info=True)
                return Response({"detail": "An unexpected error occurred during registration. Please try again later."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                refresh = CustomRefreshToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
                
                # Track the access token with device information
                device_type = request.data.get('device_type', 'web')
                try:
                    # Save the token details to database
                    AccessToken.objects.create(
                        user=user,
                        token_jti=refresh["jti"],  # JWT ID
                        device_type=device_type,
                        device_name=request.META.get('HTTP_USER_AGENT', ''),
                        ip_address=self.get_client_ip(request)
                    )
                except Exception as e:
                    # Don't fail registration if token tracking fails
                    logger.error(f"Token tracking error for user {user.id}: {e}", exc_info=True)
                    
            except Exception as e:
                logger.error(f"Token generation error for user {user.id}: {e}", exc_info=True)
                return Response({"detail": "User registered, but token generation failed. Please try logging in."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            user_data = UserProfileSerializer(user).data
            return Response({
                'user': user_data,
                'tokens': tokens,
                'message': f'{user.get_user_type_display()} registered successfully'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(BaseRegistrationView):
    """Generic user registration view"""
    serializer_class = UserRegistrationSerializer


class CustomerRegistrationView(BaseRegistrationView):
    """Customer registration view"""
    serializer_class = CustomerRegistrationSerializer


class ProviderRegistrationView(BaseRegistrationView):
    """Service provider registration view"""
    serializer_class = ProviderRegistrationSerializer


class AdminRegistrationView(BaseRegistrationView):
    """Admin registration view"""
    serializer_class = AdminRegistrationSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating the authenticated user's profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            logger.warning(f"User profile update validation failed for user {request.user.id}: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_update(serializer)
        except IntegrityError as e:
            logger.error(f"User profile update IntegrityError for user {request.user.id}: {e}", exc_info=True)
            # Check for common unique constraint violations
            err_str = str(e).lower()
            error_detail = {}
            if 'username' in err_str:
                error_detail['username'] = ['A user with that username already exists.']
            elif 'email' in err_str:
                error_detail['email'] = ['A user with that email address already exists.']
            elif 'phone_number' in err_str and request.data.get('phone_number'):
                error_detail['phone_number'] = ['A user with that phone number already exists.']
            else:
                error_detail['detail'] = 'An integrity error occurred. Some information might already be in use.'
            return Response(error_detail, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            logger.error(f"User profile update DatabaseError for user {request.user.id}: {e}", exc_info=True)
            return Response({"detail": "A database error occurred while updating the profile."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error during user profile update for user {request.user.id}: {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred while updating the profile."}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    # perform_update is called by update, so we don't need to override it 
    # if we handle exceptions in the update method itself as done above.
    # However, if we wanted to keep the update method cleaner and closer to DRF's original,
    # we would put the try-except block for serializer.save() inside perform_update.
    # For this implementation, the above update method modification is sufficient.


class CustomerProfileView(UserProfileView):
    """View for retrieving and updating the customer's profile"""
    permission_classes = [permissions.IsAuthenticated, IsCustomer]


class ProviderProfileView(UserProfileView):
    """View for retrieving and updating the service provider's profile"""
    permission_classes = [permissions.IsAuthenticated, IsServiceProvider]


class AdminProfileView(UserProfileView):
    """View for retrieving and updating the admin's profile"""
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

class UserPublicProfileView(generics.RetrieveAPIView):
    """View for retrieving a user's public profile"""
    serializer_class = PublicUserProfileSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()
    lookup_field = 'id'

class UserAvatarUploadView(APIView):
    """View for uploading or changing user profile picture"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Check if the request contains an image file
        if 'profile_picture' not in request.FILES:
            logger.warning(f"User {user.id} attempted avatar upload without providing a file.")
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['profile_picture']

        # File type validation
        ALLOWED_AVATAR_TYPES = ['image/jpeg', 'image/png', 'image/gif']
        if uploaded_file.content_type not in ALLOWED_AVATAR_TYPES:
            logger.warning(f"User {user.id} attempted to upload an invalid file type for avatar: {uploaded_file.content_type}")
            return Response({
                'error': f"Invalid file type. Allowed types are: {', '.join(ALLOWED_AVATAR_TYPES)}."
            }, status=status.HTTP_400_BAD_REQUEST)

        # File size validation (e.g., 2MB limit)
        MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
        if uploaded_file.size > MAX_AVATAR_SIZE:
            logger.warning(f"User {user.id} attempted to upload an avatar exceeding size limit: {uploaded_file.size} bytes.")
            return Response({
                'error': f"File size exceeds the limit of {MAX_AVATAR_SIZE // (1024 * 1024)}MB."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Update the user's profile picture
            user.profile_picture = request.FILES['profile_picture']
            user.save()
            
            # Return updated user profile
            serializer = UserProfileSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except (IOError, OSError) as e:
            logger.error(f"File system error during avatar upload for user {user.id}: {e}", exc_info=True)
            return Response({'error': 'A file system error occurred while saving the avatar. Please try again.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except DatabaseError as e:
            logger.error(f"Database error during avatar upload for user {user.id}: {e}", exc_info=True)
            return Response({'error': 'A database error occurred while saving the avatar. Please try again.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error during avatar upload for user {user.id}: {e}", exc_info=True)
            return Response({'error': 'An unexpected error occurred while uploading the avatar. Please try again.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileImageUploadView(APIView):
    """View for uploading or changing user profile image (alternate endpoint)"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Check if the request contains an image file
        if 'profile_image' not in request.FILES:
            logger.warning(f"User {user.id} attempted profile image upload without providing a file.")
            return Response({'error': 'No image file provided'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['profile_image']

        # File type validation
        ALLOWED_AVATAR_TYPES = ['image/jpeg', 'image/png', 'image/gif'] # Consider moving to settings or constants file
        if uploaded_file.content_type not in ALLOWED_AVATAR_TYPES:
            logger.warning(f"User {user.id} attempted to upload an invalid file type for profile image: {uploaded_file.content_type}")
            return Response({
                'error': f"Invalid file type. Allowed types are: {', '.join(ALLOWED_AVATAR_TYPES)}."
            }, status=status.HTTP_400_BAD_REQUEST)

        # File size validation (e.g., 2MB limit)
        MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB. Consider moving to settings or constants file
        if uploaded_file.size > MAX_AVATAR_SIZE:
            logger.warning(f"User {user.id} attempted to upload a profile image exceeding size limit: {uploaded_file.size} bytes.")
            return Response({
                'error': f"File size exceeds the limit of {MAX_AVATAR_SIZE // (1024 * 1024)}MB."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Update the user's profile picture
            user.profile_picture = request.FILES['profile_image']  # Map profile_image to profile_picture field
            user.save()
            
            # Return updated user profile
            serializer = UserProfileSerializer(user)
            return Response({
                'message': 'Profile image uploaded successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        except (IOError, OSError) as e:
            logger.error(f"File system error during profile image upload for user {user.id}: {e}", exc_info=True)
            return Response({'error': 'A file system error occurred while saving the profile image. Please try again.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except DatabaseError as e:
            logger.error(f"Database error during profile image upload for user {user.id}: {e}", exc_info=True)
            return Response({'error': 'A database error occurred while saving the profile image. Please try again.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error during profile image upload for user {user.id}: {e}", exc_info=True)
            return Response({'error': 'An unexpected error occurred while uploading the profile image. Please try again.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileLikeView(APIView):
    """View for liking/matching with another user profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, id, *args, **kwargs):
        target_user = get_object_or_404(User, id=id)
        current_user = request.user

        if target_user == current_user:
            return Response({'error': 'You cannot like your own profile.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .models import Like
            
            like, created = Like.objects.get_or_create(
                user_liking=current_user,
                user_liked=target_user
            )

            if created:
                return Response({
                    'message': f'Successfully liked {target_user.username}.',
                    'status': 'liked'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'message': f'You have already liked {target_user.username}.',
                    'status': 'already_liked'
                }, status=status.HTTP_200_OK) 

        except IntegrityError as e:
            logger.warning(f"IntegrityError when {current_user.username} tried to like {target_user.username}: {e}")
            return Response({'error': 'Could not process like due to a data conflict. You might have already liked this profile.'},
                            status=status.HTTP_409_CONFLICT)
        except DatabaseError as e:
            logger.error(f"DatabaseError when {current_user.username} liking {target_user.username}: {e}", exc_info=True)
            return Response({'error': 'A database error occurred. Please try again.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ImportError:
            logger.error(f"Like model not found. Ensure it is created and imported correctly.", exc_info=True)
            return Response({'error': 'Server configuration error: Like functionality is not available.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error when {current_user.username} liking {target_user.username}: {e}", exc_info=True)
            return Response({'error': 'An unexpected error occurred. Please try again.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfilePassView(APIView):
    """View for passing on another user profile (rejecting a match)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, id, *args, **kwargs):
        # Get the target user
        target_user = get_object_or_404(User, id=id)
        current_user = request.user
        
        # In a real implementation, you'd record this preference in a database
        # For now, we'll just return a success message
        return Response({
            'message': f'Passed on profile for {target_user.username}',
            'status': 'success'
        }, status=status.HTTP_200_OK)


class UserSearchByPhoneView(APIView):
    """View for searching users by phone number from request body"""
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_for_user(self, user):
        """Return the appropriate serializer based on user type"""
        if user.user_type == 'customer':
            return CustomerSearchResultSerializer(user)
        elif user.user_type == 'provider':
            return ProviderSearchResultSerializer(user)
        elif user.user_type == 'admin':
            return AdminSearchResultSerializer(user)
        else:
            return CustomerSearchResultSerializer(user)  # default
    
    def post(self, request, *args, **kwargs):
        # Get phone number from request body
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({
                'message': 'Phone number is required',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # First try exact match (for performance and accuracy)
            exact_match = User.objects.filter(phone_number=phone_number).first()
            if exact_match:
                serializer = self.get_serializer_for_user(exact_match)
                return Response({
                    'message': 'User found with exact phone match',
                    'user': serializer.data,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
            
            # If no exact match, try partial match
            partial_matches = User.objects.filter(phone_number__icontains=phone_number)
            
            if not partial_matches.exists():
                return Response({
                    'message': 'No users found with the given phone number',
                    'users': [],
                    'status': 'not_found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Process partial match results
            results = []
            for user_obj in partial_matches: 
                serializer = self.get_serializer_for_user(user_obj)
                results.append(serializer.data)
            
            return Response({
                'message': f'Found {partial_matches.count()} user(s) with similar phone numbers',
                'users': results,
                'status': 'success'
            }, status=status.HTTP_200_OK)
        except DatabaseError as e:
            logger.error(f"Database error during user search by phone for {request.user.id if request.user.is_authenticated else 'anonymous'} with phone {phone_number}: {e}", exc_info=True)
            return Response({
                'message': 'A database error occurred while searching by phone number.',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error during user search by phone for {request.user.id if request.user.is_authenticated else 'anonymous'} with phone {phone_number}: {e}", exc_info=True)
            return Response({
                'message': 'An unexpected error occurred while searching by phone number.',
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSearchView(APIView):
    """View for searching users by various criteria using request body for advanced filtering
    
    Role-based searching functionality:
    - Providers can search for customers
    - Customers can search for providers
    - Admins can search for both providers and customers
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_for_user(self, user):
        """Return the appropriate serializer based on user type"""
        if user.user_type == 'customer':
            return CustomerSearchResultSerializer(user)
        elif user.user_type == 'provider':
            return ProviderSearchResultSerializer(user)
        elif user.user_type == 'admin':
            return AdminSearchResultSerializer(user)
        else:
            return CustomerSearchResultSerializer(user)  # default
    
    def post(self, request, *args, **kwargs):
        # Get search parameters from request body
        data = request.data
        
        # Apply role-based search restrictions
        user_type = request.user.user_type
        
        # Start with all users and filter based on provided criteria
        queryset = User.objects.all()
        
        # Apply role-based filtering
        if user_type == 'customer':
            # Customers can only search for providers
            queryset = queryset.filter(user_type='provider')
        elif user_type == 'provider':
            # Providers can only search for customers
            queryset = queryset.filter(user_type='customer')
        elif user_type == 'admin':
            # Admins can search for both customers and providers but not other admins by default
            # If specifically requested to include admins, allow it
            if data.get('include_admins', False):
                queryset = queryset.exclude(id=request.user.id)  # Exclude self
            else:
                queryset = queryset.filter(Q(user_type='customer') | Q(user_type='provider'))
        
        # Initialize the filter
        filters = Q()
        
        # General search term (searches across multiple fields)
        search_term = data.get('search_term')
        if search_term:
            term_filter = Q(username__icontains=search_term) | \
                         Q(email__icontains=search_term) | \
                         Q(phone_number__icontains=search_term) | \
                         Q(first_name__icontains=search_term) | \
                         Q(last_name__icontains=search_term)
            filters &= term_filter
        
        # Filter by exact fields if provided
        if 'username' in data and data['username']:
            filters &= Q(username__icontains=data['username'])
            
        if 'email' in data and data['email']:
            filters &= Q(email__icontains=data['email'])
            
        if 'phone_number' in data and data['phone_number']:
            filters &= Q(phone_number__icontains=data['phone_number'])
            
        if 'name' in data and data['name']:
            name_filter = Q(first_name__icontains=data['name']) | Q(last_name__icontains=data['name'])
            filters &= name_filter
        
        # Filter by user types (can be a list)
        # Note: user_types filtering is now secondary to the role-based restrictions
        user_types = data.get('user_types', [])
        
        # Get the current user's role
        current_user_role = request.user.user_type
        
        if user_types:
            # Filter the requested user types based on what the current user role is allowed to search
            allowed_types = []
            
            if current_user_role == 'customer':
                # Customers can only search providers
                allowed_types = [t for t in user_types if t == 'provider']
            elif current_user_role == 'provider':
                # Providers can only search customers
                allowed_types = [t for t in user_types if t == 'customer']
            elif current_user_role == 'admin':
                # Admins can search providers and customers, and admins if specifically requested
                if data.get('include_admins', False):
                    allowed_types = [t for t in user_types if t in ['customer', 'provider', 'admin']]
                else:
                    allowed_types = [t for t in user_types if t in ['customer', 'provider']]
            
            # Apply filters only if allowed types exist
            if allowed_types:
                type_filter = Q()
                for allowed_type in allowed_types:
                    type_filter |= Q(user_type=allowed_type)
                filters &= type_filter
        elif 'user_type' in data and data['user_type']:  # For backward compatibility
            requested_type = data['user_type']
            
            # Check if the requested type is allowed for the current user role
            if ((current_user_role == 'customer' and requested_type == 'provider') or
                (current_user_role == 'provider' and requested_type == 'customer') or
                (current_user_role == 'admin' and requested_type in ['customer', 'provider']) or
                (current_user_role == 'admin' and requested_type == 'admin' and data.get('include_admins', False))):
                
                filters &= Q(user_type=requested_type)
        
        # Filter by verification status
        if 'is_verified' in data:
            filters &= Q(is_verified=data['is_verified'])
            
        if 'is_email_verified' in data:
            filters &= Q(is_email_verified=data['is_email_verified'])
            
        if 'is_phone_verified' in data:
            filters &= Q(is_phone_verified=data['is_phone_verified'])
        
        # Filter by location
        if 'location' in data and data['location']:
            filters &= Q(location__icontains=data['location'])
        
        # Filter by provider-specific fields
        if 'min_rating' in data and data['min_rating'] is not None:
            filters &= Q(rating__gte=data['min_rating'])
            
        if 'max_rating' in data and data['max_rating'] is not None:
            filters &= Q(rating__lte=data['max_rating'])
            
        if 'min_bookings' in data and data['min_bookings'] is not None:
            filters &= Q(total_bookings__gte=data['min_bookings'])
        
        # Filter by skills (for providers)
        if 'skills' in data and data['skills']:
            skills = data['skills']
            if isinstance(skills, list):
                # Complex query for JSONField with contains operator
                for skill in skills:
                    # This assumes skills are stored in a format that can be queried this way
                    # May need adjustment based on your actual JSON structure
                    filters &= Q(skills__contains={"name": skill})
        
        # Date range filters
        if 'created_after' in data and data['created_after']:
            filters &= Q(created_at__gte=data['created_after'])
            
        if 'created_before' in data and data['created_before']:
            filters &= Q(created_at__lte=data['created_before'])
        
        # Apply sorting
        sort_by = data.get('sort_by', 'created_at')
        sort_order = data.get('sort_order', 'desc')
        
        valid_sort_fields = ['username', 'first_name', 'last_name', 'created_at', 'rating', 'total_bookings']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
            
        order_prefix = '-' if sort_order.lower() == 'desc' else ''
        order_by = f'{order_prefix}{sort_by}'
        
        # Apply pagination
        try:
            page = int(data.get('page', 1))
            page_size = int(data.get('page_size', 10))
        except (ValueError, TypeError):
            logger.warning(f"Invalid pagination parameters for user search by {request.user.id}: page='{data.get('page')}', page_size='{data.get('page_size')}'")
            return Response({"detail": "Invalid page or page_size parameters. They must be integers."}, status=status.HTTP_400_BAD_REQUEST)
        
        if page < 1:
            page = 1
        # Max page size can be a setting, 100 is a common upper limit.
        # Default to 10 if outside reasonable bounds (e.g., 1 to 100).
        if not (1 <= page_size <= 100):
            page_size = 10
            
        start = (page - 1) * page_size
        end = start + page_size
        
        try:
            # Apply all filters and sorting
            if filters != Q():
                queryset = queryset.filter(filters).order_by(order_by)
            else:
                # If no filters specified, at least sort the results
                queryset = queryset.order_by(order_by)
                
            # Count total before pagination
            total_count = queryset.count()
            # Apply pagination
            queryset = queryset[start:end]
            
            if not queryset.exists():
                return Response({
                    'message': 'No users found matching the search criteria',
                    'users': [], # Keep 'users' for consistency if some clients expect it
                    'results': {}, # More generic results field
                    'total_count': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Process results by user type for customized output
            results = []
            for user_obj in queryset: # Renamed to avoid conflict with User model
                serializer = self.get_serializer_for_user(user_obj)
                results.append(serializer.data)
            
            # Get current user's role for context-aware response
            current_user_role = request.user.user_type
            
            # Create response structure based on the user's role
            response_data = {
                'message': f'Found {total_count} user(s)',
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size if total_count > 0 else 0
            }
            
            # Tailor the response based on the user's role
            if current_user_role == 'customer':
                # Customers are searching for providers
                response_data['providers'] = results
                response_data['search_context'] = 'As a customer, you are viewing service providers'
                
            elif current_user_role == 'provider':
                # Providers are searching for customers
                response_data['customers'] = results
                response_data['search_context'] = 'As a service provider, you are viewing potential customers'
                
            elif current_user_role == 'admin':
                # Admins can see all types - organize by type
                organized_results = {
                    'customers': [],
                    'providers': [],
                    'admins': []
                }
                
                for result_item in results: # Renamed to avoid conflict
                    user_type_from_result = result_item.get('user_type') # Renamed to avoid conflict
                    if user_type_from_result == 'customer':
                        organized_results['customers'].append(result_item)
                    elif user_type_from_result == 'provider':
                        organized_results['providers'].append(result_item)
                    elif user_type_from_result == 'admin':
                        organized_results['admins'].append(result_item)
                        
                response_data['results'] = organized_results
                response_data['customers_count'] = len(organized_results['customers'])
                response_data['providers_count'] = len(organized_results['providers'])
                response_data['admins_count'] = len(organized_results['admins'])
                response_data['search_context'] = 'As an admin, you are viewing all user types'
            
            return Response(response_data, status=status.HTTP_200_OK)

        except DatabaseError as e:
            logger.error(f"Database error during user search for {request.user.id} with data {data}: {e}", exc_info=True)
            return Response({"detail": "A database error occurred while searching for users. Please try again later."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error during user search for {request.user.id} with data {data}: {e}", exc_info=True)
            return Response({"detail": "An unexpected error occurred while searching for users. Please try again later."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self, request, *args, **kwargs):
        # For backward compatibility, maintain GET method with query params
        query = request.query_params.get('q', '')
        user_type = request.query_params.get('type', '')
        
        # Get additional search parameters if provided
        include_admins = request.query_params.get('include_admins', 'false').lower() == 'true'
        page = request.query_params.get('page', '1')
        page_size = request.query_params.get('page_size', '10')
        location = request.query_params.get('location', '')
        min_rating = request.query_params.get('min_rating', None)
        max_rating = request.query_params.get('max_rating', None)
        
        # Convert to POST-like structure and call post method
        request_data = {
            'search_term': query,
            'user_type': user_type,
            'include_admins': include_admins,
            'page': page,
            'page_size': page_size,
            'location': location
        }
        
        try:
            # Add optional parameters only if they're provided
            if min_rating is not None:
                request_data['min_rating'] = float(min_rating)
            if max_rating is not None:
                request_data['max_rating'] = float(max_rating)
        except ValueError:
            logger.warning(f"Invalid rating parameters for user search GET request by {request.user.id}: min_rating='{min_rating}', max_rating='{max_rating}'")
            return Response({"detail": "Invalid min_rating or max_rating parameters. They must be numbers."}, status=status.HTTP_400_BAD_REQUEST)
        
        request._full_data = request_data  # Inject data for post method
        
        return self.post(request, *args, **kwargs)


class UserVerificationView(APIView):
    """View for initiating the user verification process"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        verification_type = request.data.get('verification_type', 'identity')
        document_link = request.data.get('document_link')
        
        # Check if a verification of this type is already in progress
        from verification.models import Verification # Consider moving imports to the top of the file
        try:
            existing_verifications = Verification.objects.filter(
                user=user,
                verification_type=verification_type,
                status__in=['pending', 'in_progress']
            )
            
            if existing_verifications.exists():
                # It's good practice to log when an existing verification prevents a new one
                logger.info(f"User {user.id} attempted to start a duplicate '{verification_type}' verification.")
                return Response({
                    'status': 'error',
                    'message': f'A {verification_type} verification is already in progress.',
                    'verification_id': existing_verifications.first().id
                }, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            logger.error(f"Database error checking existing verifications for user {user.id}, type '{verification_type}': {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'A database error occurred while checking for existing verifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e: # Catch any other unexpected error during the check
            logger.error(f"Unexpected error checking existing verifications for user {user.id}, type '{verification_type}': {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred while checking for existing verifications.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            with transaction.atomic():
                # Create a new verification request
                verification = Verification.objects.create(
                    user=user,
                    verification_type=verification_type,
                    status='pending',
                    document_link=document_link
                )
                
                # In a real implementation, you would initiate any external verification API calls here
                # For example, integrating with a KYC provider
                
                # Send notification about verification initiation
                # Consider moving this import to the top of the file if not already there
                from notifications.utils import send_notification 
                send_notification(
                    recipient=user,
                    notification_type='verification_status',
                    title='Verification Process Started',
                    message=f'Your {verification_type} verification process has been initiated. Please check the verification tab for next steps.',
                    content_object=verification,
                    action_url=f'/account/verifications/{verification.id}/'
                )
                
                # Also notify admin about new verification request
                # This query could also fail, handled by the broader DatabaseError below
                for admin_user in User.objects.filter(is_staff=True): # Renamed to avoid conflict
                    send_notification(
                        recipient=admin_user,
                        notification_type='admin_alert',
                        title='New Verification Request',
                        message=f'User {user.username} has requested {verification_type} verification.',
                        content_object=verification,
                        action_url=f'/admin/verification/verification/{verification.id}/change/'
                    )
            
            logger.info(f"Verification process for '{verification_type}' initiated successfully for user {user.id}, verification ID: {verification.id}")
            return Response({
                'status': 'success',
                'message': 'Verification process initiated successfully.',
                'verification_id': verification.id,
                'document_link': document_link,
                'next_steps': 'Please upload required verification documents.'
            }, status=status.HTTP_201_CREATED)

        except DatabaseError as e:
            logger.error(f"Database error during verification process for user {user.id}, type '{verification_type}': {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'A database error occurred while initiating the verification process.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e: # Catch other exceptions, including potential ones from send_notification
            logger.error(f"Unexpected error during verification process for user {user.id}, type '{verification_type}': {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'Failed to initiate verification process. An unexpected error occurred.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# PIN Authentication Views

class PinLoginView(APIView):
    """View for authenticating users with phone number and PIN"""
    permission_classes = [permissions.AllowAny]
    serializer_class = PinLoginSerializer
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            try:
                # Generate JWT tokens
                refresh = CustomRefreshToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
                
                # Track the access token with device information
                device_type = request.data.get('device_type', 'web')
                try:
                    AccessToken.objects.create(
                        user=user,
                        token_jti=refresh["jti"],
                        device_type=device_type,
                        device_name=request.META.get('HTTP_USER_AGENT', ''),
                        ip_address=self.get_client_ip(request)
                    )
                except Exception as e:
                    logger.error(f"Token tracking error for user {user.id}: {e}", exc_info=True)
                
                # Get user profile data
                user_data = UserProfileSerializer(user).data
                
                logger.info(f"User {user.id} ({user.username}) logged in successfully with PIN")
                
                return Response({
                    'user': user_data,
                    'tokens': tokens,
                    'message': 'Login successful'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Token generation error during PIN login for user {user.id}: {e}", exc_info=True)
                return Response({
                    'detail': 'Authentication successful but token generation failed. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PinRegistrationView(BaseRegistrationView):
    """Enhanced registration view with PIN authentication"""
    serializer_class = PinRegistrationSerializer


class CustomerPinRegistrationView(PinRegistrationView):
    """Customer registration with PIN"""
    
    def get_serializer(self, *args, **kwargs):
        serializer_class = type('CustomerPinRegistrationSerializer', (PinRegistrationSerializer,), {
            'get_user_type': lambda self: 'customer'
        })
        kwargs['data'] = self.request.data
        return serializer_class(*args, **kwargs)


class ProviderPinRegistrationView(PinRegistrationView):
    """Provider registration with PIN"""
    
    def get_serializer(self, *args, **kwargs):
        serializer_class = type('ProviderPinRegistrationSerializer', (PinRegistrationSerializer,), {
            'get_user_type': lambda self: 'provider',
            'Meta': type('Meta', (), {
                'model': User,
                'fields': PinRegistrationSerializer.Meta.fields + ['skills'],
                'extra_kwargs': PinRegistrationSerializer.Meta.extra_kwargs
            })
        })
        kwargs['data'] = self.request.data
        return serializer_class(*args, **kwargs)


class ChangePinView(APIView):
    """View for changing user's PIN"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePinSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            new_pin = serializer.validated_data['new_pin']
            
            try:
                user.set_pin(new_pin)
                user.save()
                
                logger.info(f"User {user.id} ({user.username}) changed their PIN successfully")
                
                return Response({
                    'message': 'PIN changed successfully',
                    'pin_updated_at': user.pin_updated_at
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Error changing PIN for user {user.id}: {e}", exc_info=True)
                return Response({
                    'detail': 'An error occurred while changing your PIN. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPinView(APIView):
    """View for resetting user's PIN (requires phone verification)"""
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPinSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            new_pin = serializer.validated_data['new_pin']
            
            try:
                user = User.objects.get(phone_number=phone_number)
                user.set_pin(new_pin)
                user.save()
                
                logger.info(f"PIN reset successfully for user {user.id} ({user.username})")
                
                # TODO: Implement phone verification before allowing PIN reset
                # For now, we'll allow PIN reset without verification
                # In production, you should verify the phone number with OTP
                
                return Response({
                    'message': 'PIN reset successfully',
                    'pin_updated_at': user.pin_updated_at
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'detail': 'User not found with this phone number'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error resetting PIN for phone {phone_number}: {e}", exc_info=True)
                return Response({
                    'detail': 'An error occurred while resetting your PIN. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PinStatusView(APIView):
    """View for checking PIN status and lock information"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PinStatusSerializer
    
    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user)
        
        return Response({
            'pin_status': serializer.data,
            'user_id': user.id
        }, status=status.HTTP_200_OK)


class UserTypeView(APIView):
    """View for getting user type based on authentication token"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserTypeSerializer
    
    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user)
        
        return Response({
            'data': serializer.data,
            'message': f'User is a {user.get_user_type_display()}',
            'status': 'success'
        }, status=status.HTTP_200_OK)


class UserTypeChangeView(APIView):
    """View for getting user type change information and changing user type"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Get information about possible user type changes"""
        user = request.user
        current_type = user.user_type
        
        # Define allowed transitions
        allowed_transitions = {
            'customer': ['provider'],
            'provider': ['customer'],
            'admin': []  # Admins typically can't change type
        }
        
        # Define requirements for each type change
        requirements = {
            'provider': {
                'phone_number': 'Phone number is required',
                'skills': 'At least one skill must be specified',
                'verification': 'Account verification may be required'
            },
            'customer': {
                'no_pending_bookings': 'No pending service bookings',
                'profile_completion': 'Basic profile information must be complete'
            }
        }
        
        # Define restrictions
        restrictions = {
            'admin': 'Administrator accounts cannot change type',
            'pending_verification': 'Cannot change type while verification is pending',
            'active_bookings': 'Cannot change type with active bookings'
        }
        
        available_changes = allowed_transitions.get(current_type, [])
        
        info_data = {
            'current_type': current_type,
            'current_type_display': user.get_user_type_display(),
            'available_changes': [
                {
                    'type': change_type,
                    'display': dict(User.USER_TYPE_CHOICES)[change_type],
                    'requirements': requirements.get(change_type, {})
                }
                for change_type in available_changes
            ],
            'change_restrictions': restrictions,
            'requirements': requirements
        }
        
        serializer = UserTypeChangeInfoSerializer(info_data)
        
        return Response({
            'data': serializer.data,
            'message': f'User type change information for {user.get_user_type_display()}',
            'status': 'success'
        }, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        """Change user type"""
        user = request.user
        serializer = UserTypeChangeSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            to_type = serializer.validated_data['to']
            reason = serializer.validated_data.get('reason', '')
            from_type = user.user_type
            
            try:
                with transaction.atomic():
                    # Store the change for audit purposes
                    old_type = user.user_type
                    user.user_type = to_type
                    
                    # Preserve user data when changing types since users can be both customer and provider
                    # No need to clear provider-specific data when switching to customer
                    # No need to reset customer data when switching to provider
                    
                    # Initialize provider-specific data only if user doesn't have any provider experience
                    if to_type == 'provider' and old_type == 'customer':
                        # Keep existing skills if user has any, otherwise initialize empty skills
                        if user.skills is None:
                            user.skills = {}
                        # Keep existing rating and booking count (user might have been a provider before)
                    
                    # When switching to customer, preserve all provider data
                    # User might want to switch back to provider later
                    
                    user.save()
                    
                    # Log the change
                    logger.info(f"User {user.id} ({user.username}) changed type from {old_type} to {to_type}. Reason: {reason}")
                    
                    # Send notification about type change
                    try:
                        from notifications.utils import send_notification
                        send_notification(
                            recipient=user,
                            notification_type='account_update',
                            title='User Type Changed',
                            message=f'Your account type has been changed from {dict(User.USER_TYPE_CHOICES)[old_type]} to {dict(User.USER_TYPE_CHOICES)[to_type]}.',
                            action_url='/account/profile/'
                        )
                    except ImportError:
                        # Notifications app might not be available
                        pass
                    except Exception as e:
                        logger.warning(f"Failed to send notification for user type change: {e}")
                
                return Response({
                    'message': f'User type successfully changed from {dict(User.USER_TYPE_CHOICES)[from_type]} to {dict(User.USER_TYPE_CHOICES)[to_type]}',
                    'from': from_type,
                    'to': to_type,
                    'user': UserProfileSerializer(user).data,
                    'status': 'success'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"Error changing user type for user {user.id}: {e}", exc_info=True)
                return Response({
                    'detail': 'An error occurred while changing user type. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import status, generics, permissions, parsers, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import User, AccessToken, Verification # Assuming User is in users.models, if not, adjust
# Assuming Like model is in the same app's models.py. Adjust if it's elsewhere.
# from .models import Like # Or from another_app.models import Like
from django.db import transaction
from django.db.models import Q
from .tokens import CustomRefreshToken
from .permissions import IsCustomer, IsServiceProvider, IsAdmin
from .utils import StandardizedResponseHelper  # Import our new response helper

import logging
from django.db import IntegrityError, DatabaseError
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from .models import Verification
from .serializers import (
    VerificationListSerializer,
    VerificationDetailSerializer,
    VerificationCreateSerializer,
    VerificationUpdateSerializer,
    VerificationAdminUpdateSerializer
)
from .permissions import IsVerificationOwner, IsVerificationAdmin


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
        # Debug: Log the start of token listing operation
        logger.debug(f"User {request.user.id} requesting access tokens list")
        
        queryset = self.get_queryset()
        
        # Allow filtering by active status
        active_only = request.query_params.get('active_only', 'false').lower() == 'true'
        if active_only:
            queryset = queryset.filter(is_active=True)
            logger.debug(f"Filtering active tokens only: {active_only}")
            
        serializer = self.get_serializer(queryset, many=True)
        
        # Debug: Log token count before response
        token_count = queryset.count()
        logger.debug(f"Found {token_count} tokens for user {request.user.id}")
        
        # Use standardized response format
        return Response(
            StandardizedResponseHelper.success_response(
                message=f"Retrieved {token_count} access token(s)",
                data={
                    'tokens': serializer.data,
                    'count': token_count,
                    'active_only_filter': active_only
                },
                status_code=200
            ),
            status=status.HTTP_200_OK
        )


class UserAccessTokenRevokeView(APIView):
    """View for revoking a specific access token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, token_id, *args, **kwargs):
        # Debug: Log token revocation attempt
        logger.debug(f"User {request.user.id} attempting to revoke token {token_id}")
        
        try:
            # Find the token and ensure it belongs to the current user
            token = get_object_or_404(AccessToken, id=token_id, user=request.user)
            
            # Debug: Log token found
            logger.debug(f"Token {token_id} found for user {request.user.id}, device: {token.device_type}")
            
            # Mark as inactive
            token.is_active = False
            token.save(update_fields=['is_active'])
            
            # Debug: Log successful revocation
            logger.debug(f"Token {token_id} successfully revoked for user {request.user.id}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message='Token revoked successfully',
                    data={
                        'token_id': str(token_id),
                        'device_type': token.device_type,
                        'device_name': token.device_name
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error revoking token {token_id} for user {request.user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while revoking the token.",
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserAccessTokenRevokeAllView(APIView):
    """View for revoking all active access tokens for the authenticated user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        # Debug: Log revoke all tokens attempt
        logger.debug(f"User {request.user.id} attempting to revoke all active tokens")
        
        try:
            # Get all active tokens for the current user
            active_tokens = AccessToken.objects.filter(user=request.user, is_active=True)
            tokens_count = active_tokens.count()
            
            # Debug: Log token count
            logger.debug(f"Found {tokens_count} active tokens for user {request.user.id}")
            
            if tokens_count == 0:
                logger.debug(f"No active tokens found for user {request.user.id}")
                return Response(
                    StandardizedResponseHelper.success_response(
                        message='No active tokens to revoke',
                        data={
                            'revoked_count': 0,
                            'user_id': str(request.user.id)
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            
            # Mark all active tokens as inactive
            active_tokens.update(is_active=False)
            
            logger.info(f"User {request.user.id} ({request.user.username}) revoked all {tokens_count} active tokens")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message='All active tokens revoked successfully',
                    data={
                        'revoked_count': tokens_count,
                        'user_id': str(request.user.id),
                        'username': request.user.username
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error revoking all tokens for user {request.user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while revoking all tokens.",
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Note: UserLogoutView removed as part of password removal - 
# Alternative token management should be implemented if needed


class UserDeactivateView(APIView):
    """
    Allows the currently authenticated user to deactivate their own account.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Debug: Log deactivation attempt
        logger.debug(f"User {user.id} ({user.username}) attempting to deactivate account")
        
        if not user.is_active:
            logger.debug(f"User {user.id} account is already deactivated")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Account is already deactivated.",
                    data={
                        'user_id': str(user.id),
                        'username': user.username,
                        'is_active': user.is_active
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = False
        try:
            user.save(update_fields=['is_active'])
            
            # Debug: Log successful deactivation
            logger.debug(f"User {user.id} account deactivated successfully")
            
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
            return Response(
                StandardizedResponseHelper.success_response(
                    message="Account deactivated successfully.",
                    data={
                        'user_id': str(user.id),
                        'username': user.username,
                        'deactivated_at': user.updated_at.isoformat() if user.updated_at else None,
                        'is_active': user.is_active
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error deactivating account for user {user.id}: {e}", exc_info=True)
            # Re-activate user if save failed to maintain consistent state, though unlikely with just one field.
            # user.is_active = True # This might be too aggressive or cause other issues.
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while deactivating your account. Please try again.",
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
                # Debug: Log registration attempt
                email = request.data.get('email', 'N/A')
                username = request.data.get('username', 'N/A')
                logger.debug(f"Attempting to register user: email={email}, username={username}")
                
                user = serializer.save()
                
                # Debug: Log successful user creation
                logger.debug(f"User created successfully: id={user.id}, username={user.username}, email={user.email}")
                
            except IntegrityError as e:
                logger.warning(f"Registration IntegrityError for {request.data.get('email', 'N/A')}: {e}")
                error_detail = {}
                err_str = str(e).lower()
                if 'username' in err_str:
                    error_detail['username'] = 'A user with that username already exists.'
                elif 'email' in err_str:
                    error_detail['email'] = 'A user with that email address already exists.'
                elif 'phone_number' in err_str and request.data.get('phone_number'):
                     error_detail['phone_number'] = 'A user with that phone number already exists.'
                else:
                    error_detail['general'] = 'An account with some of your provided information already exists.'
                
                return Response(
                    StandardizedResponseHelper.validation_error_response(
                        serializer_errors=error_detail,
                        message="Registration failed due to duplicate information",
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
            except DatabaseError as e:
                logger.error(f"Registration DatabaseError for {request.data.get('email', 'N/A')}: {e}", exc_info=True)
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="A database error occurred during registration. Please try again later.",
                        status_code=500
                    ),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception as e:
                logger.error(f"Unexpected error during user save for {request.data.get('email', 'N/A')}: {e}", exc_info=True)
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="An unexpected error occurred during registration. Please try again later.",
                        status_code=500
                    ),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            try:
                # Debug: Log token generation attempt
                logger.debug(f"Generating tokens for user {user.id}")
                
                refresh = CustomRefreshToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
                
                # Debug: Log successful token generation
                logger.debug(f"Tokens generated successfully for user {user.id}")
                
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
                    logger.debug(f"Access token tracked in database for user {user.id}, device: {device_type}")
                except Exception as e:
                    # Don't fail registration if token tracking fails
                    logger.error(f"Token tracking error for user {user.id}: {e}", exc_info=True)
                    
            except Exception as e:
                logger.error(f"Token generation error for user {user.id}: {e}", exc_info=True)
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="User registered, but token generation failed. Please try logging in.",
                        data={'user_id': str(user.id), 'username': user.username},
                        status_code=500
                    ),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            user_data = UserProfileSerializer(user).data
            
            # Debug: Log successful registration completion
            logger.debug(f"Registration completed successfully for user {user.id} ({user.username})")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f'{user.get_user_type_display()} registered successfully',
                    data={
                        'user': user_data,
                        'tokens': tokens,
                        'registration_details': {
                            'user_type': user.user_type,
                            'user_type_display': user.get_user_type_display(),
                            'device_type': device_type
                        }
                    },
                    status_code=201
                ),
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            StandardizedResponseHelper.validation_error_response(
                serializer_errors=serializer.errors,
                message="Registration failed due to validation errors",
                status_code=400
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminRegistrationView(BaseRegistrationView):
    """Admin registration view"""
    serializer_class = AdminRegistrationSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating the authenticated user's profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        """Override GET method to return standardized response"""
        # Debug: Log profile request
        logger.debug(f"User {request.user.id} requesting their profile")
        
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response(
            StandardizedResponseHelper.success_response(
                message="User profile retrieved successfully",
                data=serializer.data,
                status_code=200
            ),
            status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Debug: Log profile update attempt
        logger.debug(f"User {request.user.id} attempting to update profile, partial={partial}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            logger.warning(f"User profile update validation failed for user {request.user.id}: {serializer.errors}")
            return Response(
                StandardizedResponseHelper.validation_error_response(
                    serializer_errors=serializer.errors,
                    message="Profile update failed due to validation errors",
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Debug: Log before saving
            logger.debug(f"Saving profile updates for user {request.user.id}")
            
            self.perform_update(serializer)
            
            # Debug: Log successful update
            logger.debug(f"Profile updated successfully for user {request.user.id}")
            
        except IntegrityError as e:
            logger.error(f"User profile update IntegrityError for user {request.user.id}: {e}", exc_info=True)
            # Check for common unique constraint violations
            err_str = str(e).lower()
            error_detail = {}
            if 'username' in err_str:
                error_detail['username'] = 'A user with that username already exists.'
            elif 'email' in err_str:
                error_detail['email'] = 'A user with that email address already exists.'
            elif 'phone_number' in err_str and request.data.get('phone_number'):
                error_detail['phone_number'] = 'A user with that phone number already exists.'
            else:
                error_detail['general'] = 'An integrity error occurred. Some information might already be in use.'
            
            return Response(
                StandardizedResponseHelper.validation_error_response(
                    serializer_errors=error_detail,
                    message="Profile update failed due to duplicate information",
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        except DatabaseError as e:
            logger.error(f"User profile update DatabaseError for user {request.user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="A database error occurred while updating the profile.",
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error during user profile update for user {request.user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An unexpected error occurred while updating the profile.",
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(
            StandardizedResponseHelper.success_response(
                message="Profile updated successfully",
                data=serializer.data,
                status_code=200
            ),
            status=status.HTTP_200_OK
        )

    # perform_update is called by update, so we don't need to override it 
    # if we handle exceptions in the update method itself as done above.
    # However, if we wanted to keep the update method cleaner and closer to DRF's original,
    # we would put the try-except block for serializer.save() inside perform_update.
    # For this implementation, the above update method modification is sufficient.


class UserPublicProfileView(generics.RetrieveAPIView):
    """View for retrieving a user's public profile"""
    serializer_class = PublicUserProfileSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()
    lookup_field = 'id'
    
    def get(self, request, *args, **kwargs):
        """Override GET method to return standardized response"""
        # Debug: Log public profile request
        user_id = kwargs.get('id', 'unknown')
        requester = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.debug(f"User {requester} requesting public profile for user {user_id}")
        
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            
            # Debug: Log successful retrieval
            logger.debug(f"Public profile retrieved successfully for user {instance.id} ({instance.username})")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message="Public profile retrieved successfully",
                    data=serializer.data,
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            logger.debug(f"Public profile not found for user ID: {user_id}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="User profile not found",
                    data={'requested_user_id': str(user_id)},
                    status_code=404
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error retrieving public profile for user {user_id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving the profile",
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProfileImageUploadView(APIView):
    """View for uploading or changing user profile image (alternate endpoint)"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Debug: Log profile image upload attempt
        logger.debug(f"User {user.id} attempting to upload profile image")
        
        # Check for different input methods
        profile_image_data = None
        
        # Check for traditional file upload
        if 'profile_image' in request.FILES:
            profile_image_data = request.FILES['profile_image']
            logger.debug(f"User {user.id} uploading profile image via file upload")
        
        # Check for JSON data with image link/base64
        elif request.data.get('profile_image'):
            profile_image_data = request.data.get('profile_image')
            logger.debug(f"User {user.id} uploading profile image via link/base64")
        
        # Check for specific image link field
        elif request.data.get('image_link'):
            profile_image_data = request.data.get('image_link')
            logger.debug(f"User {user.id} uploading profile image via image_link")
        
        # Check for base64 image field
        elif request.data.get('image_base64'):
            profile_image_data = request.data.get('image_base64')
            logger.debug(f"User {user.id} uploading profile image via base64")
        
        if not profile_image_data:
            logger.warning(f"User {user.id} attempted profile image upload without providing image data.")
            return Response(
                StandardizedResponseHelper.error_response(
                    message='No image file provided. Please provide image via file upload, URL, or base64 data.',
                    data={
                        'user_id': str(user.id),
                        'accepted_fields': ['profile_image', 'image_link', 'image_base64'],
                        'accepted_formats': ['File upload', 'URL', 'Base64 data', 'Local file path']
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Use the enhanced DocumentImageProcessor to handle any type of image input
            from .utils import DocumentImageProcessor
            
            logger.debug(f"Processing profile image for user {user.id}")
            processed_image = DocumentImageProcessor.process_profile_images(profile_image_data)
            
            if not processed_image:
                logger.warning(f"User {user.id} provided invalid image data or unsupported format.")
                return Response(
                    StandardizedResponseHelper.error_response(
                        message='Failed to process the provided image. Please check the format, size, and ensure it\'s a valid image file.',
                        data={
                            'user_id': str(user.id),
                            'supported_formats': DocumentImageProcessor.SUPPORTED_IMAGE_TYPES,
                            'max_size_mb': 5,
                            'input_type': type(profile_image_data).__name__
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update the user's profile picture with the processed image
            user.profile_picture = processed_image
            user.save(update_fields=['profile_picture'])
            
            # Debug: Log successful upload
            logger.debug(f"Profile image uploaded successfully for user {user.id}")
            
            # Return updated user profile with consistent URL formatting
            serializer = UserProfileSerializer(user)
            
            # Get file details for response
            file_details = {
                'file_name': processed_image.name,
                'file_size': processed_image.size if hasattr(processed_image, 'size') else 'unknown',
                'file_type': getattr(processed_image, 'content_type', 'unknown'),
                'processing_method': 'DocumentImageProcessor'
            }
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message='Profile image uploaded and processed successfully',
                    data={
                        'user': serializer.data,
                        'upload_details': file_details,
                        'image_url': user.profile_picture_url(request),  # Use the new method with request
                        'image_path': user.profile_picture.url if user.profile_picture else None
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except (IOError, OSError) as e:
            logger.error(f"File system error during profile image upload for user {user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='A file system error occurred while saving the profile image. Please try again.',
                    data={'user_id': str(user.id)},
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except DatabaseError as e:
            logger.error(f"Database error during profile image upload for user {user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='A database error occurred while saving the profile image. Please try again.',
                    data={'user_id': str(user.id)},
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error during profile image upload for user {user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='An unexpected error occurred while uploading the profile image. Please try again.',
                    data={'user_id': str(user.id)},
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserProfileLikeView(APIView):
    """View for liking/matching with another user profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, id, *args, **kwargs):
        # Debug: Log like attempt
        logger.debug(f"User {request.user.id} attempting to like user {id}")
        
        target_user = get_object_or_404(User, id=id)
        current_user = request.user

        if target_user == current_user:
            logger.debug(f"User {current_user.id} attempted to like their own profile")
            return Response(
                StandardizedResponseHelper.error_response(
                    message='You cannot like your own profile.',
                    data={
                        'user_id': str(current_user.id),
                        'target_user_id': str(target_user.id)
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .models import Like
            
            like, created = Like.objects.get_or_create(
                user_liking=current_user,
                user_liked=target_user
            )

            if created:
                logger.debug(f"User {current_user.id} successfully liked user {target_user.id}")
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f'Successfully liked {target_user.username}.',
                        data={
                            'like_action': 'liked',
                            'target_user': {
                                'id': str(target_user.id),
                                'username': target_user.username
                            },
                            'current_user_id': str(current_user.id)
                        },
                        status_code=201
                    ),
                    status=status.HTTP_201_CREATED
                )
            else:
                logger.debug(f"User {current_user.id} already liked user {target_user.id}")
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f'You have already liked {target_user.username}.',
                        data={
                            'like_action': 'already_liked',
                            'target_user': {
                                'id': str(target_user.id),
                                'username': target_user.username
                            },
                            'current_user_id': str(current_user.id)
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                ) 

        except IntegrityError as e:
            logger.warning(f"IntegrityError when {current_user.username} tried to like {target_user.username}: {e}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message='Could not process like due to a data conflict. You might have already liked this profile.',
                    data={
                        'current_user_id': str(current_user.id),
                        'target_user_id': str(target_user.id)
                    },
                    status_code=409
                ),
                status=status.HTTP_409_CONFLICT
            )
        except DatabaseError as e:
            logger.error(f"DatabaseError when {current_user.username} liking {target_user.username}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='A database error occurred. Please try again.',
                    data={
                        'current_user_id': str(current_user.id),
                        'target_user_id': str(target_user.id)
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except ImportError:
            logger.error(f"Like model not found. Ensure it is created and imported correctly.", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='Server configuration error: Like functionality is not available.',
                    data={
                        'current_user_id': str(current_user.id),
                        'target_user_id': str(target_user.id)
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error when {current_user.username} liking {target_user.username}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='An unexpected error occurred. Please try again.',
                    data={
                        'current_user_id': str(current_user.id),
                        'target_user_id': str(target_user.id)
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserProfilePassView(APIView):
    """View for passing on another user profile (rejecting a match)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, id, *args, **kwargs):
        # Debug: Log pass attempt
        logger.debug(f"User {request.user.id} attempting to pass on user {id}")
        
        # Get the target user
        target_user = get_object_or_404(User, id=id)
        current_user = request.user
        
        # In a real implementation, you'd record this preference in a database
        # For now, we'll just return a success message
        return Response(
            StandardizedResponseHelper.success_response(
                message=f'Passed on profile for {target_user.username}',
                data={
                    'pass_action': 'passed',
                    'target_user': {
                        'id': str(target_user.id),
                        'username': target_user.username
                    },
                    'current_user_id': str(current_user.id)
                },
                status_code=200
            ),
            status=status.HTTP_200_OK
        )


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
        # Debug: Log phone search attempt
        requester = request.user.id if request.user.is_authenticated else 'anonymous'
        logger.debug(f"User {requester} attempting to search by phone number")
        
        # Get phone number from request body
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            logger.debug(f"Phone search failed - no phone number provided by user {requester}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message='Phone number is required',
                    data={'requester': str(requester)},
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # First try exact match (for performance and accuracy)
            exact_match = User.objects.filter(phone_number=phone_number).first()
            if exact_match:
                logger.debug(f"Exact phone match found for {phone_number}: user {exact_match.id}")
                serializer = self.get_serializer_for_user(exact_match)
                return Response(
                    StandardizedResponseHelper.success_response(
                        message='User found with exact phone match',
                        data={
                            'user': serializer.data,
                            'search_details': {
                                'phone_number': phone_number,
                                'match_type': 'exact',
                                'requester': str(requester)
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            
            # If no exact match, try partial match
            partial_matches = User.objects.filter(phone_number__icontains=phone_number)
            
            if not partial_matches.exists():
                logger.debug(f"No users found with phone number: {phone_number}")
                return Response(
                    StandardizedResponseHelper.error_response(
                        message='No users found with the given phone number',
                        data={
                            'phone_number': phone_number,
                            'requester': str(requester),
                            'match_type': 'none'
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Process partial match results
            results = []
            for user_obj in partial_matches: 
                serializer = self.get_serializer_for_user(user_obj)
                results.append(serializer.data)
            
            logger.debug(f"Found {partial_matches.count()} partial matches for phone: {phone_number}")
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f'Found {partial_matches.count()} user(s) with similar phone numbers',
                    data={
                        'users': results,
                        'search_details': {
                            'phone_number': phone_number,
                            'match_type': 'partial',
                            'count': partial_matches.count(),
                            'requester': str(requester)
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
        except DatabaseError as e:
            logger.error(f"Database error during user search by phone for {requester} with phone {phone_number}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='A database error occurred while searching by phone number.',
                    data={
                        'phone_number': phone_number,
                        'requester': str(requester)
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error during user search by phone for {requester} with phone {phone_number}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='An unexpected error occurred while searching by phone number.',
                    data={
                        'phone_number': phone_number,
                        'requester': str(requester)
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Invalid page or page_size parameters. They must be integers.",
                    data={
                        'page': data.get('page'),
                        'page_size': data.get('page_size'),
                        'requester_id': str(request.user.id)
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
                logger.debug(f"No users found matching search criteria for user {request.user.id}")
                return Response(
                    StandardizedResponseHelper.error_response(
                        message='No users found matching the search criteria',
                        data={
                            'search_criteria': data,
                            'total_count': 0,
                            'page': page,
                            'page_size': page_size,
                            'total_pages': 0,
                            'requester_id': str(request.user.id),
                            'requester_type': request.user.user_type
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
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
            
            # Debug: Log successful search completion
            logger.debug(f"User search completed successfully for user {request.user.id}, found {total_count} results")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f'Found {total_count} user(s)',
                    data=response_data,
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )

        except DatabaseError as e:
            logger.error(f"Database error during user search for {request.user.id} with data {data}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="A database error occurred while searching for users. Please try again later.",
                    data={
                        'requester_id': str(request.user.id),
                        'requester_type': request.user.user_type
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error during user search for {request.user.id} with data {data}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An unexpected error occurred while searching for users. Please try again later.",
                    data={
                        'requester_id': str(request.user.id),
                        'requester_type': request.user.user_type
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
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
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Invalid min_rating or max_rating parameters. They must be numbers.",
                    data={
                        'min_rating': min_rating,
                        'max_rating': max_rating,
                        'requester_id': str(request.user.id)
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request._full_data = request_data  # Inject data for post method
        
        return self.post(request, *args, **kwargs)


class UserVerificationView(APIView):
    """View for initiating the user verification process"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        verification_type = request.data.get('verification_type', 'identity')
        document_link = request.data.get('document_link')
        document_back_link = request.data.get('document_back_link')
        document_type = request.data.get('document_type', 'other')
        document_number = request.data.get('document_number', '')
        
        # Debug: Log verification request
        logger.debug(f"User {user.id} requesting {verification_type} verification with document type: {document_type}")
        
        # Check if a verification of this type is already in progress
        try:
            existing_verifications = Verification.objects.filter(
                user=user,
                verification_type=verification_type,
                document_type=document_type,
                status__in=['pending', 'in_progress']
            )
            
            if existing_verifications.exists():
                logger.info(f"User {user.id} attempted to start a duplicate '{verification_type}' verification.")
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f'A {verification_type} verification of this document type is already in progress.',
                        data={
                            'user_id': str(user.id),
                            'verification_type': verification_type,
                            'document_type': document_type,
                            'existing_verification_id': str(existing_verifications.first().id),
                            'existing_status': existing_verifications.first().status
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
        except DatabaseError as e:
            logger.error(f"Database error checking existing verifications for user {user.id}, type '{verification_type}': {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='A database error occurred while checking for existing verifications.',
                    data={
                        'user_id': str(user.id),
                        'verification_type': verification_type
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error checking existing verifications for user {user.id}, type '{verification_type}': {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='An unexpected error occurred while checking for existing verifications.',
                    data={
                        'user_id': str(user.id),
                        'verification_type': verification_type
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            with transaction.atomic():
                # Convert document links to file objects using utility functions
                document_file = None
                document_back_file = None
                
                # Import file conversion helper
                from .utils import FileConversionHelper
                
                if document_link:
                    logger.debug(f"Converting document_link for user {user.id}: {document_link[:100]}...")
                    document_file = FileConversionHelper.process_file_field(
                        document_link, 
                        'verification_document',
                        optimize_images=True
                    )
                    if not document_file:
                        logger.warning(f"Failed to convert document_link for user {user.id}")
                        return Response(
                            StandardizedResponseHelper.error_response(
                                message='Failed to process the provided document link. Please check the URL or file format.',
                                data={
                                    'user_id': str(user.id),
                                    'verification_type': verification_type,
                                    'document_link': document_link[:100] + '...' if len(document_link) > 100 else document_link
                                },
                                status_code=400
                            ),
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                if document_back_link:
                    logger.debug(f"Converting document_back_link for user {user.id}: {document_back_link[:100]}...")
                    document_back_file = FileConversionHelper.process_file_field(
                        document_back_link, 
                        'verification_document_back',
                        optimize_images=True
                    )
                    if not document_back_file:
                        logger.warning(f"Failed to convert document_back_link for user {user.id}")
                        return Response(
                            StandardizedResponseHelper.error_response(
                                message='Failed to process the provided document back link. Please check the URL or file format.',
                                data={
                                    'user_id': str(user.id),
                                    'verification_type': verification_type,
                                    'document_back_link': document_back_link[:100] + '...' if len(document_back_link) > 100 else document_back_link
                                },
                                status_code=400
                            ),
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                # Create a new verification request
                verification = Verification.objects.create(
                    user=user,
                    verification_type=verification_type,
                    document_type=document_type,
                    document_number=document_number,
                    status='pending'
                )
                
                # Save the converted files using the verification_document_path
                if document_file:
                    verification.document_url = document_file
                if document_back_file:
                    verification.document_back_url = document_back_file
                
                verification.save()
                
                # Debug: Log successful file conversion and save
                logger.debug(f"Verification {verification.id} created with converted files for user {user.id}")
                
                # In a real implementation, you would initiate any external verification API calls here
                # For example, integrating with a KYC provider
                
                # Send notification about verification initiation
                try:
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
                    for admin_user in User.objects.filter(is_staff=True):
                        send_notification(
                            recipient=admin_user,
                            notification_type='admin_alert',
                            title='New Verification Request',
                            message=f'User {user.username} has requested {verification_type} verification.',
                            content_object=verification,
                            action_url=f'/admin/verification/verification/{verification.id}/change/'
                        )
                except ImportError:
                    # Notifications app not available
                    logger.debug("Notifications app not available, skipping notification sending")
                    pass
                except Exception as e:
                    # Non-critical error, log but don't fail the verification
                    logger.warning(f"Failed to send notifications for verification {verification.id}: {e}")
            
            logger.info(f"Verification process for '{verification_type}' initiated successfully for user {user.id}, verification ID: {verification.id}")
            return Response(
                StandardizedResponseHelper.success_response(
                    message='Verification process initiated successfully.',
                    data={
                        'verification': {
                            'id': str(verification.id),
                            'type': verification_type,
                            'document_type': document_type,
                            'status': verification.status,
                            'document_number': document_number,
                            'has_document': bool(verification.document_url),
                            'has_document_back': bool(verification.document_back_url),
                            'document_filename': verification.document_filename,
                            'created_at': verification.created_at.isoformat()
                        },
                        'user_id': str(user.id),
                        'next_steps': 'Your verification documents have been uploaded and are being processed.',
                        'process_details': {
                            'initiated_at': verification.created_at.isoformat(),
                            'estimated_processing_time': '2-5 business days',
                            'documents_processed': {
                                'primary_document': bool(document_file),
                                'back_document': bool(document_back_file)
                            }
                        }
                    },
                    status_code=201
                ),
                status=status.HTTP_201_CREATED
            )

        except DatabaseError as e:
            logger.error(f"Database error during verification process for user {user.id}, type '{verification_type}': {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='A database error occurred while initiating the verification process.',
                    data={
                        'user_id': str(user.id),
                        'verification_type': verification_type,
                        'document_type': document_type
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error during verification process for user {user.id}, type '{verification_type}': {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='Failed to initiate verification process. An unexpected error occurred.',
                    data={
                        'user_id': str(user.id),
                        'verification_type': verification_type,
                        'document_type': document_type
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
        # Debug: Log login attempt
        phone_number = request.data.get('phone_number', 'N/A')
        logger.debug(f"PIN login attempt for phone: {phone_number}")
        
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Debug: Log user found
            logger.debug(f"PIN login user found: {user.id} ({user.username})")
            
            try:
                # Generate JWT tokens
                refresh = CustomRefreshToken.for_user(user)
                tokens = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
                
                # Debug: Log token generation success
                logger.debug(f"JWT tokens generated successfully for user {user.id}")
                
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
                    logger.debug(f"Access token tracking saved for user {user.id}, device: {device_type}")
                except Exception as e:
                    logger.error(f"Token tracking error for user {user.id}: {e}", exc_info=True)
                
                # Get user profile data
                user_data = UserProfileSerializer(user).data
                
                logger.info(f"User {user.id} ({user.username}) logged in successfully with PIN")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message='Login successful',
                        data={
                            'user': user_data,
                            'tokens': tokens,
                            'login_details': {
                                'device_type': device_type,
                                'login_method': 'PIN',
                                'ip_address': self.get_client_ip(request)
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
                
            except Exception as e:
                logger.error(f"Token generation error during PIN login for user {user.id}: {e}", exc_info=True)
                return Response(
                    StandardizedResponseHelper.error_response(
                        message='Authentication successful but token generation failed. Please try again.',
                        data={'user_id': str(user.id)},
                        status_code=500
                    ),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            StandardizedResponseHelper.validation_error_response(
                serializer_errors=serializer.errors,
                message="PIN login failed due to validation errors",
                status_code=400
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


class PinRegistrationView(BaseRegistrationView):
    """Enhanced registration view with PIN authentication"""
    serializer_class = PinRegistrationSerializer


class ChangePinView(APIView):
    """View for changing user's PIN"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePinSerializer
    
    def post(self, request, *args, **kwargs):
        # Debug: Log PIN change attempt
        logger.debug(f"User {request.user.id} attempting to change PIN")
        
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = request.user
            new_pin = serializer.validated_data['new_pin']
            
            # Debug: Log PIN validation success
            logger.debug(f"PIN change validation passed for user {user.id}")
            
            try:
                user.set_pin(new_pin)
                user.save()
                
                # Debug: Log successful PIN change
                logger.debug(f"PIN updated successfully for user {user.id}")
                
                logger.info(f"User {user.id} ({user.username}) changed their PIN successfully")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message='PIN changed successfully',
                        data={
                            'user_id': str(user.id),
                            'username': user.username,
                            'pin_updated_at': user.pin_updated_at.isoformat() if user.pin_updated_at else None,
                            'pin_change_details': {
                                'changed_by': 'user_request',
                                'ip_address': request.META.get('REMOTE_ADDR')
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
                
            except Exception as e:
                logger.error(f"Error changing PIN for user {user.id}: {e}", exc_info=True)
                return Response(
                    StandardizedResponseHelper.error_response(
                        message='An error occurred while changing your PIN. Please try again.',
                        data={'user_id': str(user.id)},
                        status_code=500
                    ),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            StandardizedResponseHelper.validation_error_response(
                serializer_errors=serializer.errors,
                message="PIN change failed due to validation errors",
                status_code=400
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


class ResetPinView(APIView):
    """View for resetting user's PIN (requires phone verification)"""
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPinSerializer
    
    def post(self, request, *args, **kwargs):
        # Debug: Log PIN reset attempt
        phone_number = request.data.get('phone_number', 'N/A')
        logger.debug(f"PIN reset attempt for phone: {phone_number}")
        
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            new_pin = serializer.validated_data['new_pin']
            
            # Debug: Log validation success
            logger.debug(f"PIN reset validation passed for phone: {phone_number}")
            
            try:
                user = User.objects.get(phone_number=phone_number)
                
                # Debug: Log user found
                logger.debug(f"User found for PIN reset: {user.id} ({user.username})")
                
                user.set_pin(new_pin)
                user.save()
                
                # Debug: Log successful PIN reset
                logger.debug(f"PIN reset successfully for user {user.id}")
                
                logger.info(f"PIN reset successfully for user {user.id} ({user.username})")
                
                # TODO: Implement phone verification before allowing PIN reset
                # For now, we'll allow PIN reset without verification
                # In production, you should verify the phone number with OTP
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message='PIN reset successfully',
                        data={
                            'user_id': str(user.id),
                            'username': user.username,
                            'phone_number': phone_number,
                            'pin_updated_at': user.pin_updated_at.isoformat() if user.pin_updated_at else None,
                            'reset_details': {
                                'method': 'phone_verification',
                                'verification_required': False,  # TODO: Change to True when verification implemented
                                'ip_address': request.META.get('REMOTE_ADDR')
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
                
            except User.DoesNotExist:
                logger.debug(f"User not found for PIN reset with phone: {phone_number}")
                return Response(
                    StandardizedResponseHelper.error_response(
                        message='User not found with this phone number',
                        data={'phone_number': phone_number},
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                logger.error(f"Error resetting PIN for phone {phone_number}: {e}", exc_info=True)
                return Response(
                    StandardizedResponseHelper.error_response(
                        message='An error occurred while resetting your PIN. Please try again.',
                        data={'phone_number': phone_number},
                        status_code=500
                    ),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            StandardizedResponseHelper.validation_error_response(
                serializer_errors=serializer.errors,
                message="PIN reset failed due to validation errors",
                status_code=400
            ),
            status=status.HTTP_400_BAD_REQUEST
        )


class PinStatusView(APIView):
    """View for checking PIN status and lock information"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PinStatusSerializer
    
    def get(self, request, *args, **kwargs):
        # Debug: Log PIN status request
        logger.debug(f"User {request.user.id} requesting PIN status")
        
        user = request.user
        serializer = self.serializer_class(user)
        
        return Response(
            StandardizedResponseHelper.success_response(
                message='PIN status retrieved successfully',
                data={
                    'pin_status': serializer.data,
                    'user_id': str(user.id),
                    'username': user.username
                },
                status_code=200
            ),
            status=status.HTTP_200_OK
        )


class UserTypeView(APIView):
    """View for getting user type based on authentication token"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserTypeSerializer
    
    def get(self, request, *args, **kwargs):
        # Debug: Log user type request
        logger.debug(f"User {request.user.id} requesting user type information")
        
        user = request.user
        serializer = self.serializer_class(user)
        
        return Response(
            StandardizedResponseHelper.success_response(
                message=f'User is a {user.get_user_type_display()}',
                data={
                    'user_type_info': serializer.data,
                    'user_id': str(user.id),
                    'username': user.username,
                    'user_type_display': user.get_user_type_display()
                },
                status_code=200
            ),
            status=status.HTTP_200_OK
        )


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
        
        return Response(
            StandardizedResponseHelper.success_response(
                message=f'User type change information for {user.get_user_type_display()}',
                data={
                    'change_info': serializer.data,
                    'user_id': str(user.id),
                    'username': user.username,
                    'current_type': current_type,
                    'current_type_display': user.get_user_type_display()
                },
                status_code=200
            ),
            status=status.HTTP_200_OK
        )
    
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
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f'User type successfully changed from {dict(User.USER_TYPE_CHOICES)[from_type]} to {dict(User.USER_TYPE_CHOICES)[to_type]}',
                        data={
                            'user_type_change': {
                                'from': from_type,
                                'to': to_type,
                                'from_display': dict(User.USER_TYPE_CHOICES)[from_type],
                                'to_display': dict(User.USER_TYPE_CHOICES)[to_type],
                                'reason': reason
                            },
                            'user': UserProfileSerializer(user).data
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
                
            except Exception as e:
                logger.error(f"Error changing user type for user {user.id}: {e}", exc_info=True)
                return Response(
                    StandardizedResponseHelper.error_response(
                        message='An error occurred while changing user type. Please try again.',
                        data={'user_id': str(user.id)},
                        status_code=500
                    ),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            StandardizedResponseHelper.validation_error_response(
                serializer_errors=serializer.errors,
                message="User type change failed due to validation errors",
                status_code=400
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

class VerificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for verification requests.
    Allows listing, retrieving, creating, and updating verification requests.
    Normal users can only view and submit their own verification requests.
    Admins can update status and provide verification notes.
    """
    queryset = Verification.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['verification_type', 'document_type', 'status']
    ordering_fields = ['created_at', 'updated_at', 'verified_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Verification.objects.none()
        if user.is_staff:
            return Verification.objects.all()
        return Verification.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VerificationDetailSerializer
        elif self.action == 'create':
            return VerificationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            if self.request.user.is_staff:
                return VerificationAdminUpdateSerializer
            return VerificationUpdateSerializer
        return VerificationListSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'mark_verified', 'mark_rejected', 'mark_in_progress']:
            # Only admins can update verification status
            return [permissions.IsAuthenticated(), IsVerificationAdmin()]
        elif self.action == 'retrieve':
            # Both owners and admins can view verification details
            return [permissions.IsAuthenticated(), IsVerificationOwner() | IsVerificationAdmin()]
        elif self.action == 'cancel':
            # Only owners can cancel their verifications
            return [permissions.IsAuthenticated(), IsVerificationOwner()]
        # List is filtered by user in get_queryset
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending verification request"""
        # Debug: Log verification cancellation attempt
        logger.debug(f"User {request.user.id} attempting to cancel verification {pk}")
        
        verification = self.get_object()
        try:
            verification.cancel(cancelled_by=request.user)
            
            logger.info(f"Verification {verification.id} cancelled successfully by user {request.user.id}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message='Verification request cancelled successfully.',
                    data={
                        'verification_id': str(verification.id),
                        'status': verification.status,
                        'cancelled_by': str(request.user.id),
                        'cancelled_at': verification.updated_at.isoformat() if verification.updated_at else None
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            logger.warning(f"Verification cancellation failed for user {request.user.id}, verification {pk}: {e}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message=str(e),
                    data={
                        'verification_id': str(pk),
                        'user_id': str(request.user.id)
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error during verification cancellation for user {request.user.id}, verification {pk}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='An unexpected error occurred while cancelling the verification.',
                    data={
                        'verification_id': str(pk),
                        'user_id': str(request.user.id)
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def mark_in_progress(self, request, pk=None):
        """Mark a verification as in progress"""
        # Debug: Log verification marking in progress attempt
        logger.debug(f"Admin {request.user.id} attempting to mark verification {pk} as in progress")
        
        verification = self.get_object()
        notes = request.data.get('verification_notes', '')
        try:
            verification.mark_as_in_progress(notes=notes, admin=request.user)
            
            logger.info(f"Verification {verification.id} marked as in progress by admin {request.user.id}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message='Verification marked as in progress.',
                    data={
                        'verification_id': str(verification.id),
                        'status': verification.status,
                        'verification_notes': verification.verification_notes,
                        'updated_by': str(request.user.id),
                        'updated_at': verification.updated_at.isoformat() if verification.updated_at else None
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            logger.warning(f"Failed to mark verification {pk} as in progress by admin {request.user.id}: {e}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message=str(e),
                    data={
                        'verification_id': str(pk),
                        'admin_id': str(request.user.id)
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error marking verification {pk} as in progress by admin {request.user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='An unexpected error occurred while updating verification status.',
                    data={
                        'verification_id': str(pk),
                        'admin_id': str(request.user.id)
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def mark_verified(self, request, pk=None):
        """Mark a verification as verified"""
        # Debug: Log verification marking as verified attempt
        logger.debug(f"Admin {request.user.id} attempting to mark verification {pk} as verified")
        
        verification = self.get_object()
        notes = request.data.get('verification_notes', '')
        try:
            verification.mark_as_verified(verified_by=request.user, notes=notes)
            
            logger.info(f"Verification {verification.id} marked as verified by admin {request.user.id}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message='Verification marked as verified successfully.',
                    data={
                        'verification_id': str(verification.id),
                        'status': verification.status,
                        'verification_notes': verification.verification_notes,
                        'verified_at': verification.verified_at.isoformat() if verification.verified_at else None,
                        'expires_at': verification.expires_at.isoformat() if verification.expires_at else None,
                        'verified_by': str(request.user.id),
                        'user_id': str(verification.user.id)
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            logger.warning(f"Failed to mark verification {pk} as verified by admin {request.user.id}: {e}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message=str(e),
                    data={
                        'verification_id': str(pk),
                        'admin_id': str(request.user.id)
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error marking verification {pk} as verified by admin {request.user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='An unexpected error occurred while marking verification as verified.',
                    data={
                        'verification_id': str(pk),
                        'admin_id': str(request.user.id)
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def mark_rejected(self, request, pk=None):
        """Mark a verification as rejected with a reason"""
        # Debug: Log verification marking as rejected attempt
        logger.debug(f"Admin {request.user.id} attempting to mark verification {pk} as rejected")
        
        verification = self.get_object()
        reason = request.data.get('rejection_reason', '')
        notes = request.data.get('verification_notes', '')
        
        if not reason:
            logger.warning(f"Admin {request.user.id} attempted to reject verification {pk} without providing a reason")
            return Response(
                StandardizedResponseHelper.error_response(
                    message='Rejection reason is required.',
                    data={
                        'verification_id': str(pk),
                        'admin_id': str(request.user.id),
                        'required_field': 'rejection_reason'
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            verification.mark_as_rejected(reason=reason, verified_by=request.user)
            if notes:
                verification.verification_notes = notes
                verification.save(update_fields=['verification_notes'])
            
            logger.info(f"Verification {verification.id} marked as rejected by admin {request.user.id} with reason: {reason}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message='Verification marked as rejected.',
                    data={
                        'verification_id': str(verification.id),
                        'status': verification.status,
                        'rejection_reason': verification.rejection_reason,
                        'verification_notes': verification.verification_notes,
                        'rejected_by': str(request.user.id),
                        'user_id': str(verification.user.id),
                        'rejected_at': verification.updated_at.isoformat() if verification.updated_at else None
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            logger.warning(f"Failed to mark verification {pk} as rejected by admin {request.user.id}: {e}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message=str(e),
                    data={
                        'verification_id': str(pk),
                        'admin_id': str(request.user.id)
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error marking verification {pk} as rejected by admin {request.user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='An unexpected error occurred while marking verification as rejected.',
                    data={
                        'verification_id': str(pk),
                        'admin_id': str(request.user.id)
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def status_summary(self, request):
        """Get summary of verification status counts"""
        # Debug: Log status summary request
        logger.debug(f"Admin {request.user.id} requesting verification status summary")
        
        if not request.user.is_staff:
            logger.warning(f"Non-admin user {request.user.id} attempted to access verification status summary")
            return Response(
                StandardizedResponseHelper.error_response(
                    message='Only administrators can access status summary.',
                    data={
                        'user_id': str(request.user.id),
                        'user_type': request.user.user_type,
                        'is_staff': request.user.is_staff
                    },
                    status_code=403
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            summary = {
                'status_summary': {},
                'type_summary': {}
            }
            
            # Get status counts
            for status_code, status_display in Verification.STATUS_CHOICES:
                count = Verification.objects.filter(status=status_code).count()
                summary['status_summary'][status_code] = {
                    'count': count,
                    'display': status_display
                }
                
            # Get type counts  
            for type_code, type_display in Verification.VERIFICATION_TYPE_CHOICES:
                count = Verification.objects.filter(verification_type=type_code).count()
                summary['type_summary'][type_code] = {
                    'count': count,
                    'display': type_display
                }
            
            # Calculate total counts
            total_verifications = Verification.objects.count()
            pending_count = summary['status_summary'].get('pending', {}).get('count', 0)
            verified_count = summary['status_summary'].get('verified', {}).get('count', 0)
            
            logger.debug(f"Verification status summary generated for admin {request.user.id}: {total_verifications} total verifications")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message='Verification status summary retrieved successfully.',
                    data={
                        'summary': summary,
                        'totals': {
                            'total_verifications': total_verifications,
                            'pending_verifications': pending_count,
                            'verified_count': verified_count
                        },
                        'requested_by': str(request.user.id),
                        'generated_at': timezone.now().isoformat()
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error generating verification status summary for admin {request.user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message='An error occurred while generating the status summary.',
                    data={
                        'admin_id': str(request.user.id)
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProfilePictureUrlTestView(APIView):
    """Test view to demonstrate absolute URL functionality for profile pictures"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Test different URL generation methods
        test_results = {
            'user_id': str(user.id),
            'username': user.username,
            'has_profile_picture': bool(user.profile_picture),
            'url_tests': {}
        }
        
        if user.profile_picture:
            # Test with request (should return absolute URL)
            absolute_url = user.profile_picture_url(request)
            
            # Test without request (should use fallback method)
            fallback_url = user.profile_picture_url()
            
            # Test direct file URL
            direct_url = user.profile_picture.url
            
            test_results['url_tests'] = {
                'absolute_url_with_request': absolute_url,
                'fallback_url_without_request': fallback_url,
                'direct_file_url': direct_url,
                'request_host': request.get_host(),
                'request_scheme': request.scheme,
                'expected_format': f"{request.scheme}://{request.get_host()}/media/profile_pictures/{user.id}/filename.ext"
            }
        else:
            test_results['url_tests'] = {
                'message': 'No profile picture uploaded for this user',
                'suggestion': 'Upload a profile picture first using the profile image upload endpoint'
            }
        
        return Response(
            StandardizedResponseHelper.success_response(
                message='Profile picture URL test results',
                data=test_results,
                status_code=200
            ),
            status=status.HTTP_200_OK
        )

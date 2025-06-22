import time
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ServiceCategory, ServiceSubCategory, Service, ServiceRequest
from .serializers import (
    ServiceCategorySerializer,
    ServiceSubCategorySerializer,
    ServiceListSerializer,
    ServiceCreateUpdateSerializer,
    ServiceDetailSerializer,
    ServiceRequestListSerializer,
    ServiceRequestCreateSerializer,
    ServiceRequestDetailSerializer
)
from .permissions import IsServiceProvider, IsOwner, IsCustomer
from .throttling import ServiceCategoryRateThrottle, ServiceSubCategoryRateThrottle, ServiceCreationRateThrottle, ServiceRequestRateThrottle
import math
import logging

# Import StandardizedResponseHelper from users app for consistent response formatting
from users.utils import StandardizedResponseHelper

# Debug: Setup comprehensive logging for services app with enhanced monitoring
logger = logging.getLogger(__name__)
logger.info("🚀 DEBUG: Services app views module loaded successfully")
logger.debug("📦 DEBUG: All imports completed - StandardizedResponseHelper, logging, and viewsets ready")
logger.debug("🔧 DEBUG: Starting services app with comprehensive response standardization")
logger.debug("📊 DEBUG: Response format will be: {message, data, time, statusCode}")

User = get_user_model()

# Debug: Log user model loading with enhanced tracking
logger.debug(f"👤 DEBUG: User model loaded: {User.__name__}")
logger.debug(f"📊 DEBUG: Services app initialized with {len([ServiceCategory, ServiceSubCategory, Service, ServiceRequest])} models")
logger.info("✅ DEBUG: Services app initialization completed - all models and utilities loaded")


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    🗂️ SERVICE CATEGORY VIEWSET - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ======================================================================
    
    CRUD ViewSet for service categories with comprehensive response standardization.
    All endpoints return consistent JSON format: {message, data, time, statusCode}
    
    FEATURES:
    - ✅ List categories with filtering and performance tracking
    - ✅ Retrieve individual category details with access logging
    - ✅ Create new categories (Admin only) with validation tracking
    - ✅ Update existing categories (Admin only) with change tracking
    - ✅ Delete categories (Admin only) with cascade impact analysis
    - ✅ Statistics endpoint for admin analytics with comprehensive metrics
    
    PERMISSIONS:
    - Read: Anyone (IsAuthenticatedOrReadOnly)
    - Write: Admin only (IsAdminUser)
    
    DEBUG ENHANCEMENTS:
    - 🔍 Request tracking with user context and timing
    - 📊 Performance monitoring with query count tracking
    - 🛡️ Permission validation logging
    - 📈 Operation success/failure metrics
    - 🔄 Data transformation tracking
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    throttle_classes = [ServiceCategoryRateThrottle]
    
    def dispatch(self, request, *args, **kwargs):
        """
        🚀 ENHANCED DISPATCH WITH COMPREHENSIVE REQUEST TRACKING
        =======================================================
        
        Overridden dispatch method to add comprehensive request logging and timing.
        Tracks every request with detailed context for debugging and monitoring.
        """
        # 📊 DEBUG: Capture request timing and generate unique ID
        start_time = time.time()
        request_id = f"cat_{int(start_time * 1000)}"  # Simple request ID for tracking
        
        logger.info(f"🚀 DEBUG [{request_id}]: ServiceCategory request initiated")
        logger.debug(f"📋 DEBUG [{request_id}]: Request details:")
        logger.debug(f"   🌐 Method: {request.method}")
        logger.debug(f"   📍 Path: {request.path}")
        logger.debug(f"   👤 User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        logger.debug(f"   🏷️ User Type: {request.user.user_type if request.user.is_authenticated else 'N/A'}")
        logger.debug(f"   🔍 Action: {getattr(self, 'action', 'unknown')}")
        logger.debug(f"   📊 Query Params: {dict(request.GET)}")
        
        # Store request context for later use
        self._request_context = {
            'request_id': request_id,
            'start_time': start_time,
            'method': request.method,
            'action': getattr(self, 'action', 'unknown'),
            'user_id': request.user.id if request.user.is_authenticated else None,
            'user_type': request.user.user_type if request.user.is_authenticated else None,
        }
        
        try:
            # 🔄 DEBUG: Process the request
            logger.debug(f"🔄 DEBUG [{request_id}]: Processing request through parent dispatch")
            response = super().dispatch(request, *args, **kwargs)
            
            # 📊 DEBUG: Log successful completion
            duration = time.time() - start_time
            logger.info(f"✅ DEBUG [{request_id}]: Request completed successfully in {duration:.3f}s")
            logger.debug(f"📈 DEBUG [{request_id}]: Response status: {response.status_code}")
            
            return response
            
        except Exception as e:
            # 💥 DEBUG: Log any errors during dispatch
            duration = time.time() - start_time
            logger.error(f"💥 DEBUG [{request_id}]: Request failed after {duration:.3f}s: {str(e)}")
            logger.error(f"🔍 DEBUG [{request_id}]: Error type: {type(e).__name__}")
            raise
    
    def get_queryset(self):
        """
        🔍 ENHANCED QUERYSET WITH COMPREHENSIVE FILTERING AND PERFORMANCE TRACKING
        ========================================================================
        
        Returns categories based on filtering parameters with detailed performance tracking.
        Monitors query performance and provides insights into data access patterns.
        """
        # 📝 DEBUG: Log queryset request initiation
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        logger.debug(f"🔍 DEBUG [{request_id}]: ServiceCategory queryset building started")
        
        # 📊 DEBUG: Track database query performance
        from django.db import connection
        initial_query_count = len(connection.queries)
        
        # 🏗️ DEBUG: Build base queryset
        logger.debug(f"🏗️ DEBUG [{request_id}]: Building base queryset - ServiceCategory.objects.all()")
        queryset = ServiceCategory.objects.all()
        initial_count = queryset.count()
        logger.debug(f"📊 DEBUG [{request_id}]: Base queryset contains {initial_count} total categories")
        
        # 🔍 DEBUG: Apply filtering based on parameters
        logger.debug(f"🔍 DEBUG [{request_id}]: Checking for filtering parameters")
        active_only = self.request.query_params.get('active_only')
        
        if active_only is not None:
            logger.debug(f"🎯 DEBUG [{request_id}]: Active filter parameter detected: '{active_only}'")
            
            if active_only.lower() == 'true':
                logger.debug(f"✅ DEBUG [{request_id}]: Applying active_only=true filter")
                queryset = queryset.filter(is_active=True)
                
            elif active_only.lower() == 'false':
                logger.debug(f"❌ DEBUG [{request_id}]: Applying active_only=false filter")
                queryset = queryset.filter(is_active=False)
                
            else:
                logger.warning(f"⚠️ DEBUG [{request_id}]: Invalid active_only value: '{active_only}' - ignoring")
        else:
            logger.debug(f"📋 DEBUG [{request_id}]: No active_only filter specified - using default filter (is_active=True)")
            # Apply default filter if no specific filter is provided
            if self.action == 'list':
                queryset = queryset.filter(is_active=True)
        
        # 📈 DEBUG: Calculate filtering impact
        filtered_count = queryset.count()
        filter_impact = initial_count - filtered_count
        
        logger.debug(f"📊 DEBUG [{request_id}]: Filtering results:")
        logger.debug(f"   📦 Initial count: {initial_count}")
        logger.debug(f"   ✅ Filtered count: {filtered_count}")
        logger.debug(f"   🔽 Filtered out: {filter_impact}")
        logger.debug(f"   📈 Reduction: {(filter_impact/initial_count*100):.1f}%" if initial_count > 0 else "   📈 Reduction: 0%")
        
        # 🗄️ DEBUG: Apply additional ordering and optimization
        logger.debug(f"🗄️ DEBUG [{request_id}]: Applying default ordering")
        queryset = queryset.order_by('sort_order', 'name')
        
        # 📊 DEBUG: Track query performance impact
        final_query_count = len(connection.queries)
        query_impact = final_query_count - initial_query_count
        logger.debug(f"🗃️ DEBUG [{request_id}]: Database performance:")
        logger.debug(f"   📊 Queries executed: {query_impact}")
        logger.debug(f"   🎯 Final queryset ready: {filtered_count} categories")
        
        # 🎉 DEBUG: Log successful queryset completion
        logger.info(f"✅ DEBUG [{request_id}]: Queryset built successfully - {filtered_count} categories ready for {self.action}")
        
        return queryset
    
    def get_permissions(self):
        """
        🔐 ENHANCED PERMISSION HANDLING WITH DETAILED LOGGING
        ====================================================
        
        Dynamic permission handling with comprehensive logging for security auditing.
        Tracks permission decisions and provides detailed context for access control.
        """
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        action = self.action
        user = self.request.user
        
        logger.debug(f"🔐 DEBUG [{request_id}]: Permission check initiated for action '{action}'")
        logger.debug(f"👤 DEBUG [{request_id}]: User context:")
        logger.debug(f"   🏷️ Username: {user.username if user.is_authenticated else 'Anonymous'}")
        logger.debug(f"   🔑 Authenticated: {user.is_authenticated}")
        logger.debug(f"   👑 Is Staff: {user.is_staff if user.is_authenticated else False}")
        logger.debug(f"   🎭 User Type: {user.user_type if user.is_authenticated else 'N/A'}")
        
        # 🛡️ DEBUG: Determine required permissions based on action
        admin_only_actions = ['create', 'update', 'partial_update', 'destroy', 'statistics']
        
        if action in admin_only_actions:
            logger.debug(f"🔒 DEBUG [{request_id}]: Admin-only action detected - requiring IsAdminUser permission")
            logger.debug(f"👑 DEBUG [{request_id}]: Admin check result: {user.is_staff if user.is_authenticated else False}")
            
            if user.is_authenticated and user.is_staff:
                logger.info(f"✅ DEBUG [{request_id}]: Admin permission GRANTED for '{action}'")
            else:
                logger.warning(f"🚫 DEBUG [{request_id}]: Admin permission DENIED for '{action}' - insufficient privileges")
                
            return [permissions.IsAdminUser()]
        else:
            logger.debug(f"🔓 DEBUG [{request_id}]: Public action detected - allowing authenticated or read-only access")
            logger.info(f"✅ DEBUG [{request_id}]: Public permission GRANTED for '{action}'")
            return [permissions.IsAuthenticatedOrReadOnly()]

    def list(self, request, *args, **kwargs):
        """
        📋 ENHANCED LIST METHOD WITH STANDARDIZED RESPONSE
        =================================================
        
        Enhanced list method that returns categories with standardized response format.
        Provides comprehensive logging and performance tracking.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        logger.debug(f"📋 DEBUG [{request_id}]: ServiceCategory list method initiated")
        
        try:
            # 🔍 DEBUG: Get queryset and apply pagination
            queryset = self.filter_queryset(self.get_queryset())
            initial_count = queryset.count()
            logger.debug(f"📊 DEBUG [{request_id}]: Filtered queryset contains {initial_count} categories")
            
            # 📄 DEBUG: Handle pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.debug(f"📄 DEBUG [{request_id}]: Paginated response - {len(page)} categories per page")
                
                # Get pagination info
                paginator_response = self.get_paginated_response(serializer.data)
                
                return Response(
                    StandardizedResponseHelper.paginated_response(
                        message=f"Categories retrieved successfully - page {self.paginator.page.number if hasattr(self.paginator, 'page') else 1}",
                        data=serializer.data,
                        pagination_info={
                            'current_page': self.paginator.page.number if hasattr(self.paginator, 'page') else 1,
                            'page_size': len(page),
                            'total_count': initial_count,
                            'has_next': hasattr(paginator_response.data, 'next') and paginator_response.data.get('next') is not None,
                            'has_previous': hasattr(paginator_response.data, 'previous') and paginator_response.data.get('previous') is not None
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            
            # 📊 DEBUG: Non-paginated response
            serializer = self.get_serializer(queryset, many=True)
            logger.info(f"✅ DEBUG [{request_id}]: Categories list completed - {initial_count} categories")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Categories retrieved successfully",
                    data={
                        'categories': serializer.data,
                        'summary': {
                            'total_count': initial_count,
                            'filters_applied': list(request.query_params.keys()),
                            'retrieved_at': timezone.now().isoformat()
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # 💥 DEBUG: Log list errors
            logger.error(f"💥 DEBUG [{request_id}]: Error in categories list: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving categories",
                    data={
                        'error_type': type(e).__name__,
                        'user_id': request.user.id if request.user.is_authenticated else None,
                        'filters': request.query_params.dict()
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        ➕ ENHANCED CREATE METHOD WITH STANDARDIZED RESPONSE
        ===================================================
        
        Enhanced create method that creates new categories with standardized response format.
        Provides comprehensive logging and validation tracking.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        logger.debug(f"➕ DEBUG [{request_id}]: ServiceCategory create method initiated")
        logger.debug(f"👤 DEBUG [{request_id}]: Create requested by user: {request.user.username}")
        
        try:
            # 📝 DEBUG: Log request data
            logger.debug(f"📊 DEBUG [{request_id}]: Create data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG [{request_id}]: Category data validation passed")
                
                # 💾 DEBUG: Save the category
                category = serializer.save()
                logger.info(f"✅ DEBUG [{request_id}]: Category created successfully: '{category.name}' (ID: {category.id})")
                
                # 📊 DEBUG: Log creation context
                logger.debug(f"📊 DEBUG [{request_id}]: Creation details:")
                logger.debug(f"   🏷️ Name: {category.name}")
                logger.debug(f"   📈 Sort Order: {category.sort_order}")
                logger.debug(f"   🔄 Active: {category.is_active}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Category '{category.name}' created successfully",
                        data={
                            'category': serializer.data,
                            'creation_details': {
                                'created_by': request.user.username,
                                'created_at': category.created_at.isoformat(),
                                'category_id': str(category.id)
                            }
                        },
                        status_code=201
                    ),
                    status=status.HTTP_201_CREATED
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG [{request_id}]: Category validation failed")
                logger.warning(f"🔍 DEBUG [{request_id}]: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Category validation failed",
                        data={
                            'validation_errors': serializer.errors,
                            'provided_data': request.data,
                            'error_type': 'validation_error'
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # 💥 DEBUG: Log creation errors
            logger.error(f"💥 DEBUG [{request_id}]: Error creating category: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while creating the category",
                    data={
                        'error_type': type(e).__name__,
                        'user_id': request.user.id,
                        'provided_data': request.data
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """
        🔍 ENHANCED RETRIEVE METHOD WITH STANDARDIZED RESPONSE
        =====================================================
        
        Enhanced retrieve method that gets category details with standardized response format.
        Provides comprehensive logging and access tracking.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        category_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔍 DEBUG [{request_id}]: ServiceCategory retrieve method initiated for ID: {category_id}")
        
        try:
            # 🔍 DEBUG: Get the category instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG [{request_id}]: Category found: '{instance.name}'")
            
            # 📊 DEBUG: Serialize the data
            serializer = self.get_serializer(instance)
            
            # 📈 DEBUG: Log access details
            logger.info(f"✅ DEBUG [{request_id}]: Category retrieved successfully: '{instance.name}' (ID: {instance.id})")
            logger.debug(f"👤 DEBUG [{request_id}]: Accessed by user: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Category '{instance.name}' retrieved successfully",
                    data={
                        'category': serializer.data,
                        'access_details': {
                            'accessed_by': request.user.username if request.user.is_authenticated else 'Anonymous',
                            'accessed_at': timezone.now().isoformat(),
                            'services_count': instance.services.count(),
                            'subcategories_count': instance.subcategories.count(),
                            'is_active': instance.is_active
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # 💥 DEBUG: Log retrieve errors
            logger.error(f"💥 DEBUG [{request_id}]: Error retrieving category {category_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Category not found",
                        data={
                            'category_id': category_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id if request.user.is_authenticated else None
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving the category",
                    data={
                        'error_type': type(e).__name__,
                        'category_id': category_id,
                        'user_id': request.user.id if request.user.is_authenticated else None
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, *args, **kwargs):
        """
        🔄 ENHANCED UPDATE METHOD WITH STANDARDIZED RESPONSE
        ===================================================
        
        Enhanced update method that updates categories with standardized response format.
        Provides comprehensive logging and change tracking.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        category_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔄 DEBUG [{request_id}]: ServiceCategory update method initiated for ID: {category_id}")
        logger.debug(f"👤 DEBUG [{request_id}]: Update requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the category instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG [{request_id}]: Category found for update: '{instance.name}'")
            
            # 📊 DEBUG: Store original values for change tracking
            original_data = {
                'name': instance.name,
                'description': instance.description,
                'sort_order': instance.sort_order,
                'is_active': instance.is_active
            }
            logger.debug(f"📊 DEBUG [{request_id}]: Original data captured for change tracking")
            
            # 📝 DEBUG: Log request data
            logger.debug(f"📊 DEBUG [{request_id}]: Update data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data
            serializer = self.get_serializer(instance, data=request.data)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG [{request_id}]: Category update data validation passed")
                
                # 💾 DEBUG: Save the updated category
                updated_category = serializer.save()
                logger.info(f"✅ DEBUG [{request_id}]: Category updated successfully: '{updated_category.name}' (ID: {updated_category.id})")
                
                # 🔍 DEBUG: Track changes
                changes = []
                if original_data['name'] != updated_category.name:
                    changes.append(f"name: '{original_data['name']}' → '{updated_category.name}'")
                if original_data['description'] != updated_category.description:
                    changes.append(f"description: updated")
                if original_data['sort_order'] != updated_category.sort_order:
                    changes.append(f"sort_order: {original_data['sort_order']} → {updated_category.sort_order}")
                if original_data['is_active'] != updated_category.is_active:
                    changes.append(f"is_active: {original_data['is_active']} → {updated_category.is_active}")
                
                logger.debug(f"📊 DEBUG [{request_id}]: Changes detected: {changes if changes else 'none'}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Category '{updated_category.name}' updated successfully",
                        data={
                            'category': serializer.data,
                            'update_details': {
                                'updated_by': request.user.username,
                                'updated_at': updated_category.updated_at.isoformat(),
                                'changes_made': changes,
                                'category_id': str(updated_category.id)
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG [{request_id}]: Category update validation failed")
                logger.warning(f"🔍 DEBUG [{request_id}]: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Category update validation failed",
                        data={
                            'validation_errors': serializer.errors,
                            'provided_data': request.data,
                            'category_id': category_id,
                            'error_type': 'validation_error'
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # 💥 DEBUG: Log update errors
            logger.error(f"💥 DEBUG [{request_id}]: Error updating category {category_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Category not found for update",
                        data={
                            'category_id': category_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while updating the category",
                    data={
                        'error_type': type(e).__name__,
                        'category_id': category_id,
                        'user_id': request.user.id,
                        'provided_data': request.data
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, *args, **kwargs):
        """
        🔄 ENHANCED PARTIAL UPDATE METHOD WITH STANDARDIZED RESPONSE
        ===========================================================
        
        Enhanced partial update method that updates category fields with standardized response format.
        Provides comprehensive logging and change tracking for partial updates.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        category_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔄 DEBUG [{request_id}]: ServiceCategory partial_update method initiated for ID: {category_id}")
        logger.debug(f"👤 DEBUG [{request_id}]: Partial update requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the category instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG [{request_id}]: Category found for partial update: '{instance.name}'")
            
            # 📊 DEBUG: Store original values for change tracking
            original_data = {
                'name': instance.name,
                'description': instance.description,
                'sort_order': instance.sort_order,
                'is_active': instance.is_active
            }
            logger.debug(f"📊 DEBUG [{request_id}]: Original data captured for partial update change tracking")
            
            # 📝 DEBUG: Log request data
            fields_to_update = list(request.data.keys())
            logger.debug(f"📊 DEBUG [{request_id}]: Partial update fields: {fields_to_update}")
            logger.debug(f"📊 DEBUG [{request_id}]: Partial update data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data with partial=True
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG [{request_id}]: Category partial update data validation passed")
                
                # 💾 DEBUG: Save the partially updated category
                updated_category = serializer.save()
                logger.info(f"✅ DEBUG [{request_id}]: Category partially updated successfully: '{updated_category.name}' (ID: {updated_category.id})")
                
                # 🔍 DEBUG: Track specific changes for fields that were updated
                changes = []
                if 'name' in fields_to_update and original_data['name'] != updated_category.name:
                    changes.append(f"name: '{original_data['name']}' → '{updated_category.name}'")
                if 'description' in fields_to_update and original_data['description'] != updated_category.description:
                    changes.append(f"description: updated")
                if 'sort_order' in fields_to_update and original_data['sort_order'] != updated_category.sort_order:
                    changes.append(f"sort_order: {original_data['sort_order']} → {updated_category.sort_order}")
                if 'is_active' in fields_to_update and original_data['is_active'] != updated_category.is_active:
                    changes.append(f"is_active: {original_data['is_active']} → {updated_category.is_active}")
                
                logger.debug(f"📊 DEBUG [{request_id}]: Partial update changes detected: {changes if changes else 'none'}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Category '{updated_category.name}' partially updated successfully",
                        data={
                            'category': serializer.data,
                            'partial_update_details': {
                                'updated_by': request.user.username,
                                'updated_at': updated_category.updated_at.isoformat(),
                                'fields_updated': fields_to_update,
                                'changes_made': changes,
                                'category_id': str(updated_category.id)
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG [{request_id}]: Category partial update validation failed")
                logger.warning(f"🔍 DEBUG [{request_id}]: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Category partial update validation failed",
                        data={
                            'validation_errors': serializer.errors,
                            'provided_data': request.data,
                            'fields_to_update': fields_to_update,
                            'category_id': category_id,
                            'error_type': 'validation_error'
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # 💥 DEBUG: Log partial update errors
            logger.error(f"💥 DEBUG [{request_id}]: Error partially updating category {category_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Category not found for partial update",
                        data={
                            'category_id': category_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id,
                            'fields_to_update': list(request.data.keys())
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while partially updating the category",
                    data={
                        'error_type': type(e).__name__,
                        'category_id': category_id,
                        'user_id': request.user.id,
                        'provided_data': request.data
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """
        🗑️ ENHANCED DESTROY METHOD WITH STANDARDIZED RESPONSE
        =====================================================
        
        Enhanced destroy method that deletes categories with standardized response format.
        Provides comprehensive logging and impact analysis before deletion.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        category_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🗑️ DEBUG [{request_id}]: ServiceCategory destroy method initiated for ID: {category_id}")
        logger.warning(f"🚨 DEBUG [{request_id}]: DELETION requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the category instance
            instance = self.get_object()
            logger.warning(f"🚨 DEBUG [{request_id}]: Category found for DELETION: '{instance.name}'")
            
            # 📊 DEBUG: Analyze deletion impact
            services_count = instance.services.count()
            subcategories_count = instance.subcategories.count()
            active_services_count = instance.services.filter(status='active').count()
            
            # Store details for response before deletion
            deletion_details = {
                'deleted_category': {
                    'id': str(instance.id),
                    'name': instance.name,
                    'sort_order': instance.sort_order,
                    'was_active': instance.is_active
                },
                'impact_analysis': {
                    'total_services_affected': services_count,
                    'active_services_affected': active_services_count,
                    'subcategories_affected': subcategories_count
                },
                'deletion_metadata': {
                    'deleted_by': request.user.username,
                    'deleted_at': timezone.now().isoformat(),
                    'deletion_type': 'admin_action'
                }
            }
            
            logger.warning(f"🔍 DEBUG [{request_id}]: Deletion impact analysis:")
            logger.warning(f"   📊 Total services affected: {services_count}")
            logger.warning(f"   📊 Active services affected: {active_services_count}")
            logger.warning(f"   📊 Subcategories affected: {subcategories_count}")
            logger.warning(f"   👤 Deleted by: {request.user.username}")
            
            # 🚨 DEBUG: Log critical deletion warning
            if services_count > 0:
                logger.error(f"🚨 DEBUG [{request_id}]: CRITICAL DELETION - Category has {services_count} services that will be affected!")
                
            if subcategories_count > 0:
                logger.error(f"🚨 DEBUG [{request_id}]: CRITICAL DELETION - Category has {subcategories_count} subcategories that will be affected!")
            
            # 💥 DEBUG: Perform the actual deletion
            logger.warning(f"💥 DEBUG [{request_id}]: Executing database deletion for ServiceCategory: '{instance.name}'")
            instance.delete()
            
            # ✅ DEBUG: Log successful deletion
            logger.warning(f"✅ DEBUG [{request_id}]: ServiceCategory DELETED successfully")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Category '{deletion_details['deleted_category']['name']}' deleted successfully",
                    data=deletion_details,
                    status_code=204
                ),
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            # 💥 DEBUG: Log deletion errors
            logger.error(f"💥 DEBUG [{request_id}]: Error deleting category {category_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Category not found for deletion",
                        data={
                            'category_id': category_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while deleting the category",
                    data={
                        'error_type': type(e).__name__,
                        'category_id': category_id,
                        'user_id': request.user.id,
                        'deletion_attempted_by': request.user.username
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Admin endpoint to get statistics about service distribution by category.
        Provides insights into which categories are most popular among providers and customers.
        """
        # Debug: Log statistics request
        logger.debug(f"📊 DEBUG: Category statistics requested by user {request.user.id} ({request.user.username})")
        
        # Check if the user is an admin
        if not request.user.is_staff:
            logger.warning(f"🚫 DEBUG: Non-admin user {request.user.id} attempted to access statistics endpoint")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="You do not have permission to access this endpoint",
                    data={'required_permission': 'admin', 'user_type': request.user.user_type},
                    status_code=403
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Debug: Start statistics generation
            logger.debug("🔍 DEBUG: Starting category statistics generation")
            
            # Get all active categories
            categories = ServiceCategory.objects.filter(is_active=True)
            logger.debug(f"📂 DEBUG: Found {categories.count()} active categories")
            
            # Prepare statistics
            category_stats = []
            for category in categories:
                # Debug: Processing individual category
                logger.debug(f"📁 DEBUG: Processing category: {category.name} (ID: {category.id})")
                
                # Count services in this category
                service_count = Service.objects.filter(category=category).count()
                active_service_count = Service.objects.filter(category=category, status='active').count()
                
                # Count service requests in this category
                request_count = ServiceRequest.objects.filter(category=category).count()
                open_request_count = ServiceRequest.objects.filter(category=category, status='open').count()
                
                # Count providers offering services in this category
                provider_count = User.objects.filter(
                    user_type='provider',
                    services__category=category
                ).distinct().count()
                
                # Debug: Log category metrics
                logger.debug(f"📈 DEBUG: Category {category.name} - Services: {service_count}, Requests: {request_count}, Providers: {provider_count}")
                
                # Create a stats object
                stats = {
                    'category': ServiceCategorySerializer(category).data,
                    'service_counts': {
                        'total': service_count,
                        'active': active_service_count,
                        'inactive': service_count - active_service_count
                    },
                    'request_counts': {
                        'total': request_count,
                        'open': open_request_count,
                        'fulfilled_or_expired': request_count - open_request_count
                    },
                    'provider_count': provider_count,
                    'subcategory_count': category.subcategories.count(),
                }
                
                category_stats.append(stats)
            
            # Sort by total services (descending)
            category_stats.sort(key=lambda x: x['service_counts']['total'], reverse=True)
            logger.debug(f"🔄 DEBUG: Sorted {len(category_stats)} categories by service count")
            
            # Calculate totals
            total_services = Service.objects.count()
            total_requests = ServiceRequest.objects.count()
            
            # Debug: Log final statistics
            logger.info(f"✅ DEBUG: Statistics generated successfully - Categories: {len(category_stats)}, Services: {total_services}, Requests: {total_requests}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message="Category statistics retrieved successfully",
                    data={
                        'summary': {
                            'total_categories': len(category_stats),
                            'total_services': total_services,
                            'total_requests': total_requests,
                            'generated_by': request.user.username,
                            'generated_at': timezone.now().isoformat()
                        },
                        'category_statistics': category_stats
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error generating category statistics: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while generating category statistics",
                    data={'error_type': type(e).__name__, 'admin_id': str(request.user.id)},
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

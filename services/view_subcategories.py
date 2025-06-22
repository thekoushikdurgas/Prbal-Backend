
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

class ServiceSubCategoryViewSet(viewsets.ModelViewSet):
    """
    🗂️ SERVICE SUBCATEGORY VIEWSET - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ==========================================================================
    
    CRUD ViewSet for service subcategories with comprehensive response standardization.
    All endpoints return consistent JSON format: {message, data, time, statusCode}
    
    FEATURES:
    - ✅ List subcategories with category-based filtering and performance tracking
    - ✅ Retrieve individual subcategory details with access logging
    - ✅ Create new subcategories (Admin only) with validation tracking
    - ✅ Update existing subcategories (Admin only) with change tracking
    - ✅ Delete subcategories (Admin only) with cascade impact analysis
    - ✅ Category-based filtering with detailed query optimization
    
    PERMISSIONS:
    - Read: Anyone (IsAuthenticatedOrReadOnly)
    - Write: Admin only (IsAdminUser)
    
    DEBUG ENHANCEMENTS:
    - 🔍 Request tracking with user context and timing
    - 📊 Performance monitoring with query count tracking
    - 🛡️ Permission validation logging
    - 📈 Operation success/failure metrics
    - 🔄 Data transformation and filtering tracking
    """
    queryset = ServiceSubCategory.objects.filter(is_active=True)
    serializer_class = ServiceSubCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'category']
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'sort_order', 'category__name', 'created_at']
    throttle_classes = [ServiceSubCategoryRateThrottle]
    
    def dispatch(self, request, *args, **kwargs):
        """
        🚀 ENHANCED DISPATCH WITH COMPREHENSIVE REQUEST TRACKING
        =======================================================
        
        Overridden dispatch method to add comprehensive request logging and timing.
        Tracks every subcategory request with detailed context for debugging and monitoring.
        """
        # 📊 DEBUG: Capture request timing and generate unique ID
        start_time = time.time()
        request_id = f"subcat_{int(start_time * 1000)}"  # Simple request ID for tracking
        
        logger.info(f"🚀 DEBUG [{request_id}]: ServiceSubCategory request initiated")
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
            logger.debug(f"🔄 DEBUG [{request_id}]: Processing subcategory request through parent dispatch")
            response = super().dispatch(request, *args, **kwargs)
            
            # 📊 DEBUG: Log successful completion
            duration = time.time() - start_time
            logger.info(f"✅ DEBUG [{request_id}]: SubCategory request completed successfully in {duration:.3f}s")
            logger.debug(f"📈 DEBUG [{request_id}]: Response status: {response.status_code}")
            
            return response
            
        except Exception as e:
            # 💥 DEBUG: Log any errors during dispatch
            duration = time.time() - start_time
            logger.error(f"💥 DEBUG [{request_id}]: SubCategory request failed after {duration:.3f}s: {str(e)}")
            logger.error(f"🔍 DEBUG [{request_id}]: Error type: {type(e).__name__}")
            raise
    
    def get_queryset(self):
        """
        🔍 ENHANCED QUERYSET WITH COMPREHENSIVE FILTERING AND PERFORMANCE TRACKING
        ========================================================================
        
        Returns subcategories based on filtering parameters with detailed performance tracking.
        Monitors query performance and provides insights into data access patterns.
        """
        # 📝 DEBUG: Log queryset request initiation
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        logger.debug(f"🔍 DEBUG [{request_id}]: ServiceSubCategory queryset building started")
        
        # 📊 DEBUG: Track database query performance
        from django.db import connection
        initial_query_count = len(connection.queries)
        
        # 🏗️ DEBUG: Build base queryset
        logger.debug(f"🏗️ DEBUG [{request_id}]: Building base queryset - ServiceSubCategory.objects.all()")
        queryset = ServiceSubCategory.objects.all()
        initial_count = queryset.count()
        logger.debug(f"📊 DEBUG [{request_id}]: Base queryset contains {initial_count} total subcategories")
        
        # 🔍 DEBUG: Apply filtering based on parameters
        logger.debug(f"🔍 DEBUG [{request_id}]: Checking for filtering parameters")
        filters_applied = []
        
        # Apply active_only filter if provided
        active_only = self.request.query_params.get('active_only')
        if active_only is not None:
            logger.debug(f"🎯 DEBUG [{request_id}]: Active filter parameter detected: '{active_only}'")
            
            if active_only.lower() == 'true':
                logger.debug(f"✅ DEBUG [{request_id}]: Applying active_only=true filter")
                queryset = queryset.filter(is_active=True)
                filters_applied.append('active_only=true')
                
            elif active_only.lower() == 'false':
                logger.debug(f"❌ DEBUG [{request_id}]: Applying active_only=false filter")
                queryset = queryset.filter(is_active=False)
                filters_applied.append('active_only=false')
                
            else:
                logger.warning(f"⚠️ DEBUG [{request_id}]: Invalid active_only value: '{active_only}' - ignoring")
        else:
            logger.debug(f"📋 DEBUG [{request_id}]: No active_only filter specified - using default behavior")
            
        # Apply category filter if provided
        category = self.request.query_params.get('category')
        if category:
            logger.debug(f"🏷️ DEBUG [{request_id}]: Category filter parameter detected: '{category}'")
            try:
                # Validate that the category exists
                from .models import ServiceCategory
                category_obj = ServiceCategory.objects.get(id=category)
                logger.debug(f"✅ DEBUG [{request_id}]: Category validation passed: {category_obj.name}")
                
                queryset = queryset.filter(category=category)
                filters_applied.append(f'category={category}')
                
            except ServiceCategory.DoesNotExist:
                logger.warning(f"⚠️ DEBUG [{request_id}]: Invalid category ID: '{category}' - category not found")
            except Exception as e:
                logger.warning(f"⚠️ DEBUG [{request_id}]: Error validating category '{category}': {e}")
        
        # 📈 DEBUG: Calculate filtering impact
        filtered_count = queryset.count()
        filter_impact = initial_count - filtered_count
        
        logger.debug(f"📊 DEBUG [{request_id}]: Filtering results:")
        logger.debug(f"   📦 Initial count: {initial_count}")
        logger.debug(f"   ✅ Filtered count: {filtered_count}")
        logger.debug(f"   🔽 Filtered out: {filter_impact}")
        logger.debug(f"   🎯 Filters applied: {filters_applied if filters_applied else 'none'}")
        logger.debug(f"   📈 Reduction: {(filter_impact/initial_count*100):.1f}%" if initial_count > 0 else "   📈 Reduction: 0%")
        
        # 🗄️ DEBUG: Apply additional ordering and optimization
        logger.debug(f"🗄️ DEBUG [{request_id}]: Applying default ordering (category sort, subcategory sort, name)")
        queryset = queryset.select_related('category').order_by('category__sort_order', 'sort_order', 'name')
        
        # 📊 DEBUG: Track query performance impact
        final_query_count = len(connection.queries)
        query_impact = final_query_count - initial_query_count
        logger.debug(f"🗃️ DEBUG [{request_id}]: Database performance:")
        logger.debug(f"   📊 Queries executed: {query_impact}")
        logger.debug(f"   🎯 Final queryset ready: {filtered_count} subcategories")
        logger.debug(f"   ⚡ select_related optimization applied for category data")
        
        # 🎉 DEBUG: Log successful queryset completion
        logger.info(f"✅ DEBUG [{request_id}]: SubCategory queryset built successfully - {filtered_count} subcategories ready for {self.action}")
        
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
        
        logger.debug(f"🔐 DEBUG [{request_id}]: SubCategory permission check initiated for action '{action}'")
        logger.debug(f"👤 DEBUG [{request_id}]: User context:")
        logger.debug(f"   🏷️ Username: {user.username if user.is_authenticated else 'Anonymous'}")
        logger.debug(f"   🔑 Authenticated: {user.is_authenticated}")
        logger.debug(f"   👑 Is Staff: {user.is_staff if user.is_authenticated else False}")
        logger.debug(f"   🎭 User Type: {user.user_type if user.is_authenticated else 'N/A'}")
        
        # 🛡️ DEBUG: Determine required permissions based on action
        admin_only_actions = ['create', 'update', 'partial_update', 'destroy']
        
        if action in admin_only_actions:
            logger.debug(f"🔒 DEBUG [{request_id}]: Admin-only subcategory action detected - requiring IsAdminUser permission")
            logger.debug(f"👑 DEBUG [{request_id}]: Admin check result: {user.is_staff if user.is_authenticated else False}")
            
            if user.is_authenticated and user.is_staff:
                logger.info(f"✅ DEBUG [{request_id}]: Admin permission GRANTED for subcategory '{action}'")
            else:
                logger.warning(f"🚫 DEBUG [{request_id}]: Admin permission DENIED for subcategory '{action}' - insufficient privileges")
                
            return [permissions.IsAdminUser()]
        else:
            logger.debug(f"🔓 DEBUG [{request_id}]: Public subcategory action detected - allowing authenticated or read-only access")
            logger.info(f"✅ DEBUG [{request_id}]: Public permission GRANTED for subcategory '{action}'")
            return [permissions.IsAuthenticatedOrReadOnly()]

    def list(self, request, *args, **kwargs):
        """
        📋 ENHANCED LIST METHOD WITH STANDARDIZED RESPONSE
        =================================================
        
        Enhanced list method that returns subcategories with standardized response format.
        Provides comprehensive logging and performance tracking.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        logger.debug(f"📋 DEBUG [{request_id}]: ServiceSubCategory list method initiated")
        
        try:
            # 🔍 DEBUG: Get queryset and apply pagination
            queryset = self.filter_queryset(self.get_queryset())
            initial_count = queryset.count()
            logger.debug(f"📊 DEBUG [{request_id}]: Filtered queryset contains {initial_count} subcategories")
            
            # 📄 DEBUG: Handle pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.debug(f"📄 DEBUG [{request_id}]: Paginated response - {len(page)} subcategories per page")
                
                # Get pagination info
                paginator_response = self.get_paginated_response(serializer.data)
                
                return Response(
                    StandardizedResponseHelper.paginated_response(
                        message=f"Subcategories retrieved successfully - page {self.paginator.page.number if hasattr(self.paginator, 'page') else 1}",
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
            logger.info(f"✅ DEBUG [{request_id}]: Subcategories list completed - {initial_count} subcategories")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Subcategories retrieved successfully",
                    data={
                        'subcategories': serializer.data,
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
            logger.error(f"💥 DEBUG [{request_id}]: Error in subcategories list: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving subcategories",
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
        
        Enhanced create method that creates new subcategories with standardized response format.
        Provides comprehensive logging and validation tracking.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        logger.debug(f"➕ DEBUG [{request_id}]: ServiceSubCategory create method initiated")
        logger.debug(f"👤 DEBUG [{request_id}]: Create requested by user: {request.user.username}")
        
        try:
            # 📝 DEBUG: Log request data
            logger.debug(f"📊 DEBUG [{request_id}]: Create data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG [{request_id}]: Subcategory data validation passed")
                
                # 💾 DEBUG: Save the subcategory
                subcategory = serializer.save()
                logger.info(f"✅ DEBUG [{request_id}]: Subcategory created successfully: '{subcategory.name}' (ID: {subcategory.id})")
                
                # 📊 DEBUG: Log creation context
                logger.debug(f"📊 DEBUG [{request_id}]: Creation details:")
                logger.debug(f"   🏷️ Name: {subcategory.name}")
                logger.debug(f"   📂 Category: {subcategory.category.name}")
                logger.debug(f"   📈 Sort Order: {subcategory.sort_order}")
                logger.debug(f"   🔄 Active: {subcategory.is_active}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Subcategory '{subcategory.name}' created successfully",
                        data={
                            'subcategory': serializer.data,
                            'creation_details': {
                                'created_by': request.user.username,
                                'created_at': subcategory.created_at.isoformat(),
                                'category_name': subcategory.category.name,
                                'subcategory_id': str(subcategory.id)
                            }
                        },
                        status_code=201
                    ),
                    status=status.HTTP_201_CREATED
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG [{request_id}]: Subcategory validation failed")
                logger.warning(f"🔍 DEBUG [{request_id}]: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Subcategory validation failed",
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
            logger.error(f"💥 DEBUG [{request_id}]: Error creating subcategory: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while creating the subcategory",
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
        
        Enhanced retrieve method that gets subcategory details with standardized response format.
        Provides comprehensive logging and access tracking.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        subcategory_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔍 DEBUG [{request_id}]: ServiceSubCategory retrieve method initiated for ID: {subcategory_id}")
        
        try:
            # 🔍 DEBUG: Get the subcategory instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG [{request_id}]: Subcategory found: '{instance.name}' in category '{instance.category.name}'")
            
            # 📊 DEBUG: Serialize the data
            serializer = self.get_serializer(instance)
            
            # 📈 DEBUG: Log access details
            logger.info(f"✅ DEBUG [{request_id}]: Subcategory retrieved successfully: '{instance.name}' (ID: {instance.id})")
            logger.debug(f"👤 DEBUG [{request_id}]: Accessed by user: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Subcategory '{instance.name}' retrieved successfully",
                    data={
                        'subcategory': serializer.data,
                        'access_details': {
                            'accessed_by': request.user.username if request.user.is_authenticated else 'Anonymous',
                            'accessed_at': timezone.now().isoformat(),
                            'category_name': instance.category.name,
                            'services_count': instance.services.count(),
                            'category_is_active': instance.category.is_active
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # 💥 DEBUG: Log retrieve errors
            logger.error(f"💥 DEBUG [{request_id}]: Error retrieving subcategory {subcategory_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Subcategory not found",
                        data={
                            'subcategory_id': subcategory_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id if request.user.is_authenticated else None
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving the subcategory",
                    data={
                        'error_type': type(e).__name__,
                        'subcategory_id': subcategory_id,
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
        
        Enhanced update method that updates subcategories with standardized response format.
        Provides comprehensive logging and change tracking.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        subcategory_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔄 DEBUG [{request_id}]: ServiceSubCategory update method initiated for ID: {subcategory_id}")
        logger.debug(f"👤 DEBUG [{request_id}]: Update requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the subcategory instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG [{request_id}]: Subcategory found for update: '{instance.name}' in category '{instance.category.name}'")
            
            # 📊 DEBUG: Store original values for change tracking
            original_data = {
                'name': instance.name,
                'description': instance.description,
                'category': instance.category.name,
                'sort_order': instance.sort_order,
                'is_active': instance.is_active
            }
            logger.debug(f"📊 DEBUG [{request_id}]: Original data captured for change tracking")
            
            # 📝 DEBUG: Log request data
            logger.debug(f"📊 DEBUG [{request_id}]: Update data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data
            serializer = self.get_serializer(instance, data=request.data)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG [{request_id}]: Subcategory update data validation passed")
                
                # 💾 DEBUG: Save the updated subcategory
                updated_subcategory = serializer.save()
                logger.info(f"✅ DEBUG [{request_id}]: Subcategory updated successfully: '{updated_subcategory.name}' (ID: {updated_subcategory.id})")
                
                # 🔍 DEBUG: Track changes
                changes = []
                if original_data['name'] != updated_subcategory.name:
                    changes.append(f"name: '{original_data['name']}' → '{updated_subcategory.name}'")
                if original_data['description'] != updated_subcategory.description:
                    changes.append(f"description: updated")
                if original_data['sort_order'] != updated_subcategory.sort_order:
                    changes.append(f"sort_order: {original_data['sort_order']} → {updated_subcategory.sort_order}")
                if original_data['is_active'] != updated_subcategory.is_active:
                    changes.append(f"is_active: {original_data['is_active']} → {updated_subcategory.is_active}")
                
                logger.debug(f"📊 DEBUG [{request_id}]: Changes detected: {changes if changes else 'none'}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Subcategory '{updated_subcategory.name}' updated successfully",
                        data={
                            'subcategory': serializer.data,
                            'update_details': {
                                'updated_by': request.user.username,
                                'updated_at': updated_subcategory.updated_at.isoformat(),
                                'changes_made': changes,
                                'category_name': updated_subcategory.category.name,
                                'subcategory_id': str(updated_subcategory.id)
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG [{request_id}]: Subcategory update validation failed")
                logger.warning(f"🔍 DEBUG [{request_id}]: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Subcategory update validation failed",
                        data={
                            'validation_errors': serializer.errors,
                            'provided_data': request.data,
                            'subcategory_id': subcategory_id,
                            'error_type': 'validation_error'
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # 💥 DEBUG: Log update errors
            logger.error(f"💥 DEBUG [{request_id}]: Error updating subcategory {subcategory_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Subcategory not found for update",
                        data={
                            'subcategory_id': subcategory_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while updating the subcategory",
                    data={
                        'error_type': type(e).__name__,
                        'subcategory_id': subcategory_id,
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
        
        Enhanced partial update method that updates subcategory fields with standardized response format.
        Provides comprehensive logging and change tracking for partial updates.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        subcategory_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔄 DEBUG [{request_id}]: ServiceSubCategory partial_update method initiated for ID: {subcategory_id}")
        logger.debug(f"👤 DEBUG [{request_id}]: Partial update requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the subcategory instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG [{request_id}]: Subcategory found for partial update: '{instance.name}' in category '{instance.category.name}'")
            
            # 📊 DEBUG: Store original values for change tracking
            original_data = {
                'name': instance.name,
                'description': instance.description,
                'category_name': instance.category.name,
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
                logger.debug(f"✅ DEBUG [{request_id}]: Subcategory partial update data validation passed")
                
                # 💾 DEBUG: Save the partially updated subcategory
                updated_subcategory = serializer.save()
                logger.info(f"✅ DEBUG [{request_id}]: Subcategory partially updated successfully: '{updated_subcategory.name}' (ID: {updated_subcategory.id})")
                
                # 🔍 DEBUG: Track specific changes for fields that were updated
                changes = []
                if 'name' in fields_to_update and original_data['name'] != updated_subcategory.name:
                    changes.append(f"name: '{original_data['name']}' → '{updated_subcategory.name}'")
                if 'description' in fields_to_update and original_data['description'] != updated_subcategory.description:
                    changes.append(f"description: updated")
                if 'sort_order' in fields_to_update and original_data['sort_order'] != updated_subcategory.sort_order:
                    changes.append(f"sort_order: {original_data['sort_order']} → {updated_subcategory.sort_order}")
                if 'is_active' in fields_to_update and original_data['is_active'] != updated_subcategory.is_active:
                    changes.append(f"is_active: {original_data['is_active']} → {updated_subcategory.is_active}")
                
                logger.debug(f"📊 DEBUG [{request_id}]: Partial update changes detected: {changes if changes else 'none'}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Subcategory '{updated_subcategory.name}' partially updated successfully",
                        data={
                            'subcategory': serializer.data,
                            'partial_update_details': {
                                'updated_by': request.user.username,
                                'updated_at': updated_subcategory.updated_at.isoformat(),
                                'fields_updated': fields_to_update,
                                'changes_made': changes,
                                'category_name': updated_subcategory.category.name,
                                'subcategory_id': str(updated_subcategory.id)
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG [{request_id}]: Subcategory partial update validation failed")
                logger.warning(f"🔍 DEBUG [{request_id}]: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Subcategory partial update validation failed",
                        data={
                            'validation_errors': serializer.errors,
                            'provided_data': request.data,
                            'fields_to_update': fields_to_update,
                            'subcategory_id': subcategory_id,
                            'error_type': 'validation_error'
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # 💥 DEBUG: Log partial update errors
            logger.error(f"💥 DEBUG [{request_id}]: Error partially updating subcategory {subcategory_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Subcategory not found for partial update",
                        data={
                            'subcategory_id': subcategory_id,
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
                    message="An error occurred while partially updating the subcategory",
                    data={
                        'error_type': type(e).__name__,
                        'subcategory_id': subcategory_id,
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
        
        Enhanced destroy method that deletes subcategories with standardized response format.
        Provides comprehensive logging and impact analysis before deletion.
        """
        # 📝 DEBUG: Get request context for logging
        request_id = getattr(self, '_request_context', {}).get('request_id', 'unknown')
        subcategory_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🗑️ DEBUG [{request_id}]: ServiceSubCategory destroy method initiated for ID: {subcategory_id}")
        logger.warning(f"🚨 DEBUG [{request_id}]: DELETION requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the subcategory instance
            instance = self.get_object()
            logger.warning(f"🚨 DEBUG [{request_id}]: Subcategory found for DELETION: '{instance.name}' in category '{instance.category.name}'")
            
            # 📊 DEBUG: Analyze deletion impact
            services_count = instance.services.count()
            active_services_count = instance.services.filter(status='active').count()
            
            # Store details for response before deletion
            deletion_details = {
                'deleted_subcategory': {
                    'id': str(instance.id),
                    'name': instance.name,
                    'category_name': instance.category.name,
                    'sort_order': instance.sort_order,
                    'was_active': instance.is_active
                },
                'impact_analysis': {
                    'total_services_affected': services_count,
                    'active_services_affected': active_services_count,
                    'inactive_services_affected': services_count - active_services_count
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
            logger.warning(f"   📊 Category: {instance.category.name}")
            logger.warning(f"   👤 Deleted by: {request.user.username}")
            
            # 🚨 DEBUG: Log critical deletion warning
            if services_count > 0:
                logger.error(f"🚨 DEBUG [{request_id}]: CRITICAL DELETION - Subcategory has {services_count} services that will be affected!")
                affected_services = list(instance.services.values_list('name', flat=True)[:5])
                logger.error(f"   🔍 Some affected services: {affected_services}")
                if services_count > 5:
                    logger.error(f"   📊 And {services_count - 5} more services...")
            
            # 💥 DEBUG: Perform the actual deletion
            logger.warning(f"💥 DEBUG [{request_id}]: Executing database deletion for ServiceSubCategory: '{instance.name}'")
            instance.delete()
            
            # ✅ DEBUG: Log successful deletion
            logger.warning(f"✅ DEBUG [{request_id}]: ServiceSubCategory DELETED successfully")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Subcategory '{deletion_details['deleted_subcategory']['name']}' deleted successfully",
                    data=deletion_details,
                    status_code=204
                ),
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            # 💥 DEBUG: Log deletion errors
            logger.error(f"💥 DEBUG [{request_id}]: Error deleting subcategory {subcategory_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Subcategory not found for deletion",
                        data={
                            'subcategory_id': subcategory_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while deleting the subcategory",
                    data={
                        'error_type': type(e).__name__,
                        'subcategory_id': subcategory_id,
                        'user_id': request.user.id,
                        'deletion_attempted_by': request.user.username
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

class ServiceRequestViewSet(viewsets.ModelViewSet):
    """
    📋 SERVICE REQUEST VIEWSET
    ========================
    
    CRUD ViewSet for service requests with comprehensive response standardization.
    All endpoints return consistent JSON format: {message, data, time, statusCode}
    
    FEATURES:
    - ✅ List open service requests
    - ✅ Create new service requests (Customer only)  
    - ✅ Retrieve individual request details
    - ✅ Update own requests (Owner only)
    - ✅ Delete own requests (Owner only)
    - ✅ My requests endpoint for customer history
    - ✅ Admin view for all requests
    - ✅ Recommended providers endpoint
    - ✅ Batch expire functionality (Admin)
    - ✅ Cancel request functionality
    
    PERMISSIONS:
    - Read: Anyone (AllowAny for public browsing)
    - Create: Customers only (IsCustomer)
    - Update/Delete: Owner only (IsOwner)
    
    DEBUG: All responses are tracked and logged for monitoring
    """
    queryset = ServiceRequest.objects.filter(status='open', expires_at__gt=timezone.now())
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'urgency', 'is_featured', 'customer']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'expires_at', 'budget_max']
    
    def get_queryset(self):
        """
        🔍 Enhanced queryset with role-based filtering and debug tracking
        Returns service requests based on user type and permissions
        """
        # Debug: Log queryset request
        logger.debug(f"📋 DEBUG: ServiceRequest queryset requested by user {self.request.user.id if self.request.user.is_authenticated else 'anonymous'} for action {self.action}")
        
        # For list view, only show open, non-expired requests
        if self.action == 'list':
            queryset = ServiceRequest.objects.filter(
                status='open',
                expires_at__gt=timezone.now()
            )
            logger.debug(f"📊 DEBUG: List view - returning {queryset.count()} open requests")
            return queryset
            
        # For other actions like retrieve, or for the owner, show all their requests
        elif self.request.user.is_authenticated:
            if self.request.user.is_staff:
                queryset = ServiceRequest.objects.all()
                logger.debug(f"👑 DEBUG: Admin access - returning all {queryset.count()} requests")
                return queryset
            elif self.request.user.user_type == 'customer':
                # If it's their own requests, show all regardless of status
                queryset = ServiceRequest.objects.filter(
                    Q(status='open', expires_at__gt=timezone.now()) | 
                    Q(customer=self.request.user)
                )
                logger.debug(f"🛒 DEBUG: Customer access - returning {queryset.count()} requests (open + own)")
                return queryset
            elif self.request.user.user_type == 'provider':
                # Show open requests and ones assigned to this provider
                queryset = ServiceRequest.objects.filter(
                    Q(status='open', expires_at__gt=timezone.now()) | 
                    Q(assigned_provider=self.request.user)
                )
                logger.debug(f"🔧 DEBUG: Provider access - returning {queryset.count()} requests (open + assigned)")
                return queryset
                
        # Default case - just open, non-expired requests
        queryset = ServiceRequest.objects.filter(status='open', expires_at__gt=timezone.now())
        logger.debug(f"📊 DEBUG: Default access - returning {queryset.count()} open requests")
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action in ['update', 'partial_update']:
            return ServiceRequestCreateSerializer
        elif self.action == 'retrieve':
            return ServiceRequestDetailSerializer
        return ServiceRequestListSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            # Only customers can create service requests
            return [permissions.IsAuthenticated(), IsCustomer()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only the owner can update or delete a request
            return [permissions.IsAuthenticated(), IsOwner()]
        # Anyone can view service requests
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        # Set the customer to the current user and status to open
        serializer.save(customer=self.request.user, status='open')
    
    def list(self, request, *args, **kwargs):
        """
        📋 ENHANCED LIST METHOD WITH STANDARDIZED RESPONSE
        =================================================
        
        Enhanced list method that returns service requests with standardized response format.
        Provides comprehensive logging and performance tracking.
        """
        # 📝 DEBUG: Log list request initiation
        logger.debug(f"📋 DEBUG: ServiceRequest list method initiated by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        
        try:
            # 🔍 DEBUG: Get queryset and apply filtering
            queryset = self.filter_queryset(self.get_queryset())
            initial_count = queryset.count()
            logger.debug(f"📊 DEBUG: Filtered queryset contains {initial_count} service requests")
            
            # 📄 DEBUG: Handle pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.debug(f"📄 DEBUG: Paginated response - {len(page)} service requests per page")
                
                # Get pagination info
                paginator_response = self.get_paginated_response(serializer.data)
                
                return Response(
                    StandardizedResponseHelper.paginated_response(
                        message=f"Service requests retrieved successfully - page {self.paginator.page.number if hasattr(self.paginator, 'page') else 1}",
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
            logger.info(f"✅ DEBUG: Service requests list completed - {initial_count} requests")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Service requests retrieved successfully",
                    data={
                        'service_requests': serializer.data,
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
            logger.error(f"💥 DEBUG: Error in service requests list: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving service requests",
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
        
        Enhanced create method that creates new service requests with standardized response format.
        Provides comprehensive logging and validation tracking.
        """
        # 📝 DEBUG: Log create request initiation
        logger.debug(f"➕ DEBUG: ServiceRequest create method initiated by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        logger.debug(f"👤 DEBUG: Create requested by user: {request.user.username}")
        
        try:
            # 📝 DEBUG: Log request data
            logger.debug(f"📊 DEBUG: Create data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG: ServiceRequest data validation passed")
                
                # 💾 DEBUG: Save the service request
                self.perform_create(serializer)
                service_request = serializer.instance
                logger.info(f"✅ DEBUG: ServiceRequest created successfully: '{service_request.title}' (ID: {service_request.id})")
                
                # 📊 DEBUG: Log creation context
                logger.debug(f"📊 DEBUG: Creation details:")
                logger.debug(f"   🏷️ Title: {service_request.title}")
                logger.debug(f"   📂 Category: {service_request.category.name}")
                logger.debug(f"   💰 Budget: {service_request.budget_min}-{service_request.budget_max} {service_request.currency}")
                logger.debug(f"   🔄 Status: {service_request.status}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Service request '{service_request.title}' created successfully",
                        data={
                            'service_request': serializer.data,
                            'creation_details': {
                                'created_by': request.user.username,
                                'created_at': service_request.created_at.isoformat(),
                                'category_name': service_request.category.name,
                                'request_id': str(service_request.id),
                                'status': service_request.status,
                                'expires_at': service_request.expires_at.isoformat() if service_request.expires_at else None
                            }
                        },
                        status_code=201
                    ),
                    status=status.HTTP_201_CREATED
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG: ServiceRequest validation failed")
                logger.warning(f"🔍 DEBUG: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Service request validation failed",
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
            logger.error(f"💥 DEBUG: Error creating service request: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while creating the service request",
                    data={
                        'error_type': type(e).__name__,
                        'user_id': request.user.id if request.user.is_authenticated else None,
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
        
        Enhanced retrieve method that gets service request details with standardized response format.
        Provides comprehensive logging and access tracking.
        """
        # 📝 DEBUG: Get request ID for logging
        request_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔍 DEBUG: ServiceRequest retrieve method initiated for ID: {request_id}")
        
        try:
            # 🔍 DEBUG: Get the service request instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG: ServiceRequest found: '{instance.title}' by customer '{instance.customer.username}'")
            
            # 📊 DEBUG: Serialize the data
            serializer = self.get_serializer(instance)
            
            # 📈 DEBUG: Log access details
            logger.info(f"✅ DEBUG: ServiceRequest retrieved successfully: '{instance.title}' (ID: {instance.id})")
            logger.debug(f"👤 DEBUG: Accessed by user: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Service request '{instance.title}' retrieved successfully",
                    data={
                        'service_request': serializer.data,
                        'access_details': {
                            'accessed_by': request.user.username if request.user.is_authenticated else 'Anonymous',
                            'accessed_at': timezone.now().isoformat(),
                            'customer_name': instance.customer.username,
                            'category_name': instance.category.name,
                            'request_status': instance.status,
                            'urgency': instance.urgency
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # 💥 DEBUG: Log retrieve errors
            logger.error(f"💥 DEBUG: Error retrieving service request {request_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Service request not found",
                        data={
                            'request_id': request_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id if request.user.is_authenticated else None
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving the service request",
                    data={
                        'error_type': type(e).__name__,
                        'request_id': request_id,
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
        
        Enhanced update method that updates service requests with standardized response format.
        Provides comprehensive logging and change tracking.
        """
        # 📝 DEBUG: Get request ID for logging
        request_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔄 DEBUG: ServiceRequest update method initiated for ID: {request_id}")
        logger.debug(f"👤 DEBUG: Update requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the service request instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG: ServiceRequest found for update: '{instance.title}' by customer '{instance.customer.username}'")
            
            # 📊 DEBUG: Store original values for change tracking
            original_data = {
                'title': instance.title,
                'description': instance.description,
                'budget_min': instance.budget_min,
                'budget_max': instance.budget_max,
                'urgency': instance.urgency,
                'status': instance.status
            }
            logger.debug(f"📊 DEBUG: Original data captured for change tracking")
            
            # 📝 DEBUG: Log request data
            logger.debug(f"📊 DEBUG: Update data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data
            serializer = self.get_serializer(instance, data=request.data)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG: ServiceRequest update data validation passed")
                
                # 💾 DEBUG: Save the updated service request
                updated_request = serializer.save()
                logger.info(f"✅ DEBUG: ServiceRequest updated successfully: '{updated_request.title}' (ID: {updated_request.id})")
                
                # 🔍 DEBUG: Track changes
                changes = []
                if original_data['title'] != updated_request.title:
                    changes.append(f"title: '{original_data['title']}' → '{updated_request.title}'")
                if original_data['budget_min'] != updated_request.budget_min:
                    changes.append(f"budget_min: {original_data['budget_min']} → {updated_request.budget_min}")
                if original_data['budget_max'] != updated_request.budget_max:
                    changes.append(f"budget_max: {original_data['budget_max']} → {updated_request.budget_max}")
                if original_data['urgency'] != updated_request.urgency:
                    changes.append(f"urgency: {original_data['urgency']} → {updated_request.urgency}")
                if original_data['status'] != updated_request.status:
                    changes.append(f"status: {original_data['status']} → {updated_request.status}")
                
                logger.debug(f"📊 DEBUG: Changes detected: {changes if changes else 'none'}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Service request '{updated_request.title}' updated successfully",
                        data={
                            'service_request': serializer.data,
                            'update_details': {
                                'updated_by': request.user.username,
                                'updated_at': updated_request.updated_at.isoformat(),
                                'changes_made': changes,
                                'category_name': updated_request.category.name,
                                'request_id': str(updated_request.id)
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG: ServiceRequest update validation failed")
                logger.warning(f"🔍 DEBUG: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Service request update validation failed",
                        data={
                            'validation_errors': serializer.errors,
                            'provided_data': request.data,
                            'request_id': request_id,
                            'error_type': 'validation_error'
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # 💥 DEBUG: Log update errors
            logger.error(f"💥 DEBUG: Error updating service request {request_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Service request not found for update",
                        data={
                            'request_id': request_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id if request.user.is_authenticated else None
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while updating the service request",
                    data={
                        'error_type': type(e).__name__,
                        'request_id': request_id,
                        'user_id': request.user.id if request.user.is_authenticated else None,
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
        
        Enhanced partial update method that updates service request fields with standardized response format.
        Provides comprehensive logging and change tracking for partial updates.
        """
        # 📝 DEBUG: Get request ID for logging
        request_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔄 DEBUG: ServiceRequest partial_update method initiated for ID: {request_id}")
        logger.debug(f"👤 DEBUG: Partial update requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the service request instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG: ServiceRequest found for partial update: '{instance.title}' by customer '{instance.customer.username}'")
            
            # 📊 DEBUG: Store original values for change tracking
            original_data = {
                'title': instance.title,
                'description': instance.description,
                'budget_min': instance.budget_min,
                'budget_max': instance.budget_max,
                'urgency': instance.urgency,
                'status': instance.status
            }
            logger.debug(f"📊 DEBUG: Original data captured for partial update change tracking")
            
            # 📝 DEBUG: Log request data
            fields_to_update = list(request.data.keys())
            logger.debug(f"📊 DEBUG: Partial update fields: {fields_to_update}")
            logger.debug(f"📊 DEBUG: Partial update data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data with partial=True
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG: ServiceRequest partial update data validation passed")
                
                # 💾 DEBUG: Save the partially updated service request
                updated_request = serializer.save()
                logger.info(f"✅ DEBUG: ServiceRequest partially updated successfully: '{updated_request.title}' (ID: {updated_request.id})")
                
                # 🔍 DEBUG: Track specific changes for fields that were updated
                changes = []
                if 'title' in fields_to_update and original_data['title'] != updated_request.title:
                    changes.append(f"title: '{original_data['title']}' → '{updated_request.title}'")
                if 'budget_min' in fields_to_update and original_data['budget_min'] != updated_request.budget_min:
                    changes.append(f"budget_min: {original_data['budget_min']} → {updated_request.budget_min}")
                if 'budget_max' in fields_to_update and original_data['budget_max'] != updated_request.budget_max:
                    changes.append(f"budget_max: {original_data['budget_max']} → {updated_request.budget_max}")
                if 'urgency' in fields_to_update and original_data['urgency'] != updated_request.urgency:
                    changes.append(f"urgency: {original_data['urgency']} → {updated_request.urgency}")
                if 'status' in fields_to_update and original_data['status'] != updated_request.status:
                    changes.append(f"status: {original_data['status']} → {updated_request.status}")
                
                logger.debug(f"📊 DEBUG: Partial update changes detected: {changes if changes else 'none'}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Service request '{updated_request.title}' partially updated successfully",
                        data={
                            'service_request': serializer.data,
                            'partial_update_details': {
                                'updated_by': request.user.username,
                                'updated_at': updated_request.updated_at.isoformat(),
                                'fields_updated': fields_to_update,
                                'changes_made': changes,
                                'category_name': updated_request.category.name,
                                'request_id': str(updated_request.id)
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG: ServiceRequest partial update validation failed")
                logger.warning(f"🔍 DEBUG: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Service request partial update validation failed",
                        data={
                            'validation_errors': serializer.errors,
                            'provided_data': request.data,
                            'fields_to_update': fields_to_update,
                            'request_id': request_id,
                            'error_type': 'validation_error'
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # 💥 DEBUG: Log partial update errors
            logger.error(f"💥 DEBUG: Error partially updating service request {request_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Service request not found for partial update",
                        data={
                            'request_id': request_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id if request.user.is_authenticated else None,
                            'fields_to_update': list(request.data.keys())
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while partially updating the service request",
                    data={
                        'error_type': type(e).__name__,
                        'request_id': request_id,
                        'user_id': request.user.id if request.user.is_authenticated else None,
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
        
        Enhanced destroy method that deletes service requests with standardized response format.
        Provides comprehensive logging and impact analysis before deletion.
        """
        # 📝 DEBUG: Get request ID for logging
        request_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🗑️ DEBUG: ServiceRequest destroy method initiated for ID: {request_id}")
        logger.warning(f"🚨 DEBUG: DELETION requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the service request instance
            instance = self.get_object()
            logger.warning(f"🚨 DEBUG: ServiceRequest found for DELETION: '{instance.title}' by customer '{instance.customer.username}'")
            
            # 📊 DEBUG: Analyze deletion impact
            # Check if there's an assigned provider or fulfilled service
            
            # Store details for response before deletion
            deletion_details = {
                'deleted_service_request': {
                    'id': str(instance.id),
                    'title': instance.title,
                    'customer_name': instance.customer.username,
                    'category_name': instance.category.name,
                    'budget_range': f"{instance.budget_min}-{instance.budget_max} {instance.currency}" if instance.budget_min and instance.budget_max else "Not specified",
                    'status': instance.status,
                    'urgency': instance.urgency
                },
                'impact_analysis': {
                    'assigned_provider': str(instance.assigned_provider.id) if instance.assigned_provider else None,
                    'fulfilled_by_service': str(instance.fulfilled_by_service.id) if instance.fulfilled_by_service else None,
                    'was_in_progress': instance.status == 'in_progress'
                },
                'deletion_metadata': {
                    'deleted_by': request.user.username,
                    'deleted_at': timezone.now().isoformat(),
                    'deletion_type': 'owner_action' if request.user == instance.customer else 'admin_action'
                }
            }
            
            logger.warning(f"🔍 DEBUG: Deletion impact analysis:")
            logger.warning(f"   📊 Request: {instance.title}")
            logger.warning(f"   📊 Customer: {instance.customer.username}")
            logger.warning(f"   📊 Status: {instance.status}")
            logger.warning(f"   📊 Assigned Provider: {instance.assigned_provider.username if instance.assigned_provider else 'None'}")
            logger.warning(f"   👤 Deleted by: {request.user.username}")
            
            # 💥 DEBUG: Perform the actual deletion
            logger.warning(f"💥 DEBUG: Executing database deletion for ServiceRequest: '{instance.title}'")
            instance.delete()
            
            # ✅ DEBUG: Log successful deletion
            logger.warning(f"✅ DEBUG: ServiceRequest DELETED successfully")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Service request '{deletion_details['deleted_service_request']['title']}' deleted successfully",
                    data=deletion_details,
                    status_code=204
                ),
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            # 💥 DEBUG: Log deletion errors
            logger.error(f"💥 DEBUG: Error deleting service request {request_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Service request not found for deletion",
                        data={
                            'request_id': request_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id if request.user.is_authenticated else None
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while deleting the service request",
                    data={
                        'error_type': type(e).__name__,
                        'request_id': request_id,
                        'user_id': request.user.id if request.user.is_authenticated else None,
                        'deletion_attempted_by': request.user.username
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """
        Customer-only endpoint to list their own service requests regardless of status.
        Provides customers with full visibility into their service request history.
        """
        # Debug: Log my_requests access attempt
        logger.debug(f"📋 DEBUG: My requests endpoint accessed by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        
        if not request.user.is_authenticated or request.user.user_type != 'customer':
            logger.warning(f"🚫 DEBUG: Unauthorized access to my_requests - User: {request.user.id if request.user.is_authenticated else 'anonymous'}, Type: {request.user.user_type if request.user.is_authenticated else 'N/A'}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="You do not have permission to access this endpoint",
                    data={'required_user_type': 'customer', 'current_user_type': request.user.user_type if request.user.is_authenticated else None},
                    status_code=403
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Debug: Start query processing
            logger.debug(f"🔍 DEBUG: Processing my requests for customer {request.user.id}")
            
            queryset = ServiceRequest.objects.filter(customer=request.user)
            initial_count = queryset.count()
            
            # Apply any filtering from query params
            status_filter = request.query_params.get('status')
            filters_applied = []
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
                filters_applied.append(f"status={status_filter}")
                logger.debug(f"🔍 DEBUG: Applied status filter: {status_filter}")
            
            filtered_count = queryset.count()
            logger.debug(f"📊 DEBUG: Query results - Initial: {initial_count}, Filtered: {filtered_count}")
            
            # Use the service request list serializer
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_response = self.get_paginated_response(serializer.data)
                
                # Debug: Log pagination details
                logger.debug(f"📄 DEBUG: Paginated my_requests - Page size: {len(page)}")
                
                # Extract pagination info safely
                page_number = 1
                total_pages = 1
                
                if hasattr(self.paginator, 'page'):
                    page_number = self.paginator.page.number
                    total_pages = self.paginator.page.paginator.num_pages
                elif hasattr(paginated_response, 'data'):
                    # Try to extract from paginated response data
                    if isinstance(paginated_response.data, dict):
                        # Check for common pagination fields
                        if 'current_page' in paginated_response.data:
                            page_number = paginated_response.data['current_page']
                        if 'total_pages' in paginated_response.data:
                            total_pages = paginated_response.data['total_pages']
                
                # Convert to standardized format
                return Response(
                    StandardizedResponseHelper.paginated_response(
                        message=f"Customer service requests retrieved successfully",
                        data=serializer.data,
                        pagination_info={
                            'current_page': page_number,
                            'page_size': len(page),
                            'total_count': filtered_count,
                            'total_pages': total_pages
                        },
                        status_code=200,
                        customer_info={
                            'customer_id': request.user.id,
                            'initial_count': initial_count,
                            'filtered_count': filtered_count,
                            'filters_applied': filters_applied
                        }
                    ),
                    status=status.HTTP_200_OK
                )
            
            serializer = self.get_serializer(queryset, many=True)
            
            # Debug: Log non-paginated response
            logger.info(f"✅ DEBUG: Customer requests retrieved successfully - {filtered_count} requests for customer {request.user.id}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Customer service requests retrieved successfully",
                    data={
                        'requests': serializer.data,
                        'summary': {
                            'total_count': filtered_count,
                            'initial_count': initial_count,
                            'filters_applied': filters_applied,
                            'customer_id': request.user.id,
                            'retrieved_at': timezone.now().isoformat()
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error retrieving customer requests for user {request.user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving your service requests",
                    data={
                        'error_type': type(e).__name__,
                        'customer_id': request.user.id,
                        'applied_filters': request.query_params.dict()
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=False, methods=['get'])
    def admin(self, request):
        """
        Admin-only endpoint to list all service requests regardless of status.
        Provides full visibility for administrators to manage the platform.
        """
        # Debug: Log admin request access
        logger.debug(f"🔧 DEBUG: Admin service requests view requested by user {request.user.id} ({request.user.username})")
        
        if not request.user.is_staff:
            logger.warning(f"🚫 DEBUG: Non-admin user {request.user.id} attempted to access admin service requests endpoint")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="You do not have permission to access this endpoint",
                    data={'required_permission': 'admin', 'user_type': request.user.user_type if request.user.is_authenticated else None},
                    status_code=403
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Debug: Start admin query processing
            logger.debug("🔍 DEBUG: Starting admin service requests query processing")
            
            # Get all service requests without filtering by status
            queryset = ServiceRequest.objects.all()
            initial_count = queryset.count()
            logger.debug(f"📊 DEBUG: Initial service request count: {initial_count}")
            
            # Apply any filtering from query params
            filters_applied = []
            
            category = request.query_params.get('category')
            if category:
                queryset = queryset.filter(category__id=category)
                filters_applied.append(f"category={category}")
                
            customer = request.query_params.get('customer')
            if customer:
                queryset = queryset.filter(customer__id=customer)
                filters_applied.append(f"customer={customer}")
                
            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
                filters_applied.append(f"status={status_filter}")
            
            # Debug: Log filtering results
            filtered_count = queryset.count()
            logger.debug(f"🔍 DEBUG: Applied filters: {filters_applied if filters_applied else 'none'}")
            logger.debug(f"📊 DEBUG: Filtered service request count: {filtered_count} (from {initial_count})")
            
            # Use the list serializer for the response
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_response = self.get_paginated_response(serializer.data)
                
                # Debug: Log pagination details
                logger.debug(f"📄 DEBUG: Paginated response - page size: {len(page)}")
                
                # Extract pagination info safely
                page_number = 1
                total_pages = 1
                
                if hasattr(self.paginator, 'page'):
                    page_number = self.paginator.page.number
                    total_pages = self.paginator.page.paginator.num_pages
                elif hasattr(paginated_response, 'data') and isinstance(paginated_response.data, dict):
                    # Try to extract from paginated response data
                    if 'current_page' in paginated_response.data:
                        page_number = paginated_response.data['current_page']
                    if 'total_pages' in paginated_response.data:
                        total_pages = paginated_response.data['total_pages']
                
                # Convert to standardized format
                return Response(
                    StandardizedResponseHelper.paginated_response(
                        message="Admin service requests retrieved successfully",
                        data=serializer.data,
                        pagination_info={
                            'current_page': page_number,
                            'page_size': len(page),
                            'total_count': filtered_count,
                            'total_pages': total_pages
                        },
                        status_code=200,
                        admin_filters=filters_applied,
                        query_summary={
                            'initial_count': initial_count,
                            'filtered_count': filtered_count,
                            'requested_by': request.user.username
                        }
                    ),
                    status=status.HTTP_200_OK
                )
            
            serializer = self.get_serializer(queryset, many=True)
            
            # Debug: Log non-paginated response
            logger.info(f"✅ DEBUG: Admin service requests retrieved successfully - total: {filtered_count} requests")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message="Admin service requests retrieved successfully",
                    data={
                        'service_requests': serializer.data,
                        'query_summary': {
                            'total_count': filtered_count,
                            'initial_count': initial_count,
                            'filters_applied': filters_applied,
                            'requested_by': request.user.username,
                            'retrieved_at': timezone.now().isoformat()
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error in admin service requests query: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving admin service requests",
                    data={
                        'error_type': type(e).__name__,
                        'admin_id': str(request.user.id),
                        'applied_filters': request.query_params.dict()
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=True, methods=['get'])
    def recommended_providers(self, request, pk=None):
        """
        🎯 CUSTOMER ENDPOINT: GET RECOMMENDED PROVIDERS
        =============================================
        
        Customer endpoint to get recommended providers for a specific service request.
        Returns providers who offer services in the same category and have good ratings.
        
        FEATURES:
        - ✅ Category-based provider matching
        - ✅ Active services filtering
        - ✅ Permission validation
        - ✅ Comprehensive debug logging
        - ✅ Standardized response format
        
        PERMISSIONS: Customer only (owner of request) or Admin
        DEBUG: All operations are tracked and logged
        """
        # 🔍 DEBUG: Log recommended providers request
        logger.debug(f"🎯 DEBUG: Recommended providers requested for service request {pk} by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        
        try:
            service_request = ServiceRequest.objects.get(pk=pk)
            logger.debug(f"📋 DEBUG: Service request found: {service_request.title} (Category: {service_request.category.name})")
        except ServiceRequest.DoesNotExist:
            logger.warning(f"❌ DEBUG: Service request {pk} not found")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Service request not found",
                    data={
                        'request_id': pk,
                        'error_type': 'not_found',
                        'requester_id': request.user.id if request.user.is_authenticated else None
                    },
                    status_code=404
                ),
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if the user is authorized to view recommendations
        if service_request.customer != request.user and not request.user.is_staff:
            logger.warning(f"🚫 DEBUG: Unauthorized access to provider recommendations - User {request.user.id} not owner of request {pk}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="You do not have permission to view provider recommendations for this request",
                    data={
                        'request_id': pk,
                        'owner_id': service_request.customer.id,
                        'requester_id': request.user.id,
                        'error_type': 'permission_denied'
                    },
                    status_code=403
                ),
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            # 🔍 DEBUG: Start provider recommendation process
            logger.debug(f"🔍 DEBUG: Starting provider recommendation for category: {service_request.category.name}")
            
            # Find providers who offer services in the same category
            from users.serializers import PublicUserProfileSerializer
            
            # Get providers with active services in this category
            providers = User.objects.filter(
                user_type='provider',
                services__category=service_request.category,
                services__status='active'
            ).distinct()
            
            initial_count = providers.count()
            logger.debug(f"📊 DEBUG: Found {initial_count} providers with active services in category {service_request.category.name}")
            
            # In a real implementation, we would also sort by rating, distance, etc.
            # For now, order by most recent activity
            providers = providers.order_by('-last_login', '-date_joined')
            
            serializer = PublicUserProfileSerializer(providers, many=True)
            
            # 🎉 SUCCESS: Providers found and serialized
            logger.info(f"✅ DEBUG: Recommended providers retrieved successfully - {initial_count} providers for request {pk}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Found {initial_count} recommended providers for your request",
                    data={
                        'service_request': ServiceRequestDetailSerializer(service_request).data,
                        'recommended_providers': serializer.data,
                        'recommendation_criteria': {
                            'category': service_request.category.name,
                            'provider_requirements': {
                                'user_type': 'provider',
                                'service_status': 'active',
                                'category_match': True
                            },
                            'sorting': 'most_recent_activity',
                            'location': service_request.location
                        },
                        'recommendation_summary': {
                            'total_providers': initial_count,
                            'request_id': pk,
                            'generated_at': timezone.now().isoformat()
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error generating provider recommendations for request {pk}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while finding recommended providers",
                    data={
                        'error_type': type(e).__name__,
                        'request_id': pk,
                        'category': service_request.category.name if service_request else None
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_expire(self, request):
        """
        🔧 ADMIN-ONLY ACTION: BATCH EXPIRE SERVICE REQUESTS
        =================================================
        
        Admin-only action to expire all service requests that have passed their expiration date.
        This helps keep the marketplace clean and up-to-date.
        
        FEATURES:
        - ✅ Finds expired but still open requests
        - ✅ Batch updates status to 'expired'
        - ✅ Admin permission validation
        - ✅ Comprehensive debug logging
        - ✅ Standardized response format
        - ✅ Operation audit trail
        
        PERMISSIONS: Admin only
        DEBUG: All operations are tracked and logged
        """
        # 🔍 DEBUG: Log batch expire request
        logger.debug(f"🔧 DEBUG: Batch expire service requests requested by user {request.user.id if request.user.is_authenticated else 'anonymous'} ({request.user.username if request.user.is_authenticated else 'anonymous'})")
        
        # 🔐 PERMISSION CHECK: Admin authentication
        if not request.user.is_staff:
            logger.warning(f"🚫 DEBUG: Non-admin user {request.user.id if request.user.is_authenticated else 'anonymous'} attempted to access batch expire endpoint")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="You do not have permission to perform this action",
                    data={
                        'required_permission': 'admin',
                        'current_user_type': request.user.user_type if request.user.is_authenticated else None,
                        'action': 'batch_expire_service_requests',
                        'user_id': request.user.id if request.user.is_authenticated else None
                    },
                    status_code=403
                ),
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            # 🔍 DEBUG: Start batch expire process
            logger.debug("🔍 DEBUG: Starting batch expire process for service requests")
            
            # Find all expired but still open requests
            current_time = timezone.now()
            expired_requests = ServiceRequest.objects.filter(
                status='open',
                expires_at__lt=current_time
            )
            
            initial_count = expired_requests.count()
            logger.debug(f"📊 DEBUG: Found {initial_count} expired service requests to process")
            
            if initial_count == 0:
                logger.info("📋 DEBUG: No expired service requests found to process")
                return Response(
                    StandardizedResponseHelper.success_response(
                        message="No expired service requests found to process",
                        data={
                            'operation': 'batch_expire',
                            'expired_count': 0,
                            'processed_at': current_time.isoformat(),
                            'performed_by': request.user.username,
                            'admin_id': request.user.id,
                            'search_criteria': {
                                'status': 'open',
                                'expires_before': current_time.isoformat()
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            
            # Track expired request details for audit
            expired_request_details = []
            
            # Mark them all as expired
            for req in expired_requests:
                expired_request_details.append({
                    'request_id': str(req.id),
                    'title': req.title,
                    'customer_id': str(req.customer.id),
                    'expired_at': req.expires_at.isoformat(),
                    'processed_at': current_time.isoformat()
                })
                req.mark_as_expired()
                
            processed_count = len(expired_request_details)
            
            # 🎉 SUCCESS: Requests expired successfully
            logger.info(f"✅ DEBUG: Batch expire completed successfully - {processed_count} service requests expired by admin {request.user.id}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Successfully expired {processed_count} service requests",
                    data={
                        'operation': 'batch_expire_service_requests',
                        'expired_count': processed_count,
                        'operation_summary': {
                            'initial_count': initial_count,
                            'processed_count': processed_count,
                            'performed_by': request.user.username,
                            'admin_id': request.user.id,
                            'timestamp': current_time.isoformat()
                        },
                        'search_criteria': {
                            'status': 'open',
                            'expires_before': current_time.isoformat()
                        },
                        'audit_trail': {
                            'operation_type': 'batch_status_update',
                            'old_status': 'open',
                            'new_status': 'expired',
                            'processed_requests': expired_request_details[:10]  # Limit to first 10 for response size
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error in batch expire operation: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while expiring service requests",
                    data={
                        'error_type': type(e).__name__,
                        'operation': 'batch_expire',
                        'admin_id': request.user.id,
                        'attempted_at': timezone.now().isoformat()
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        🛑 CUSTOMER-ONLY ACTION: CANCEL SERVICE REQUEST
        =============================================
        
        Customer-only action to cancel their service request.
        Allows customers to cancel their own service requests.
        
        FEATURES:
        - ✅ Permission validation (owner or admin)
        - ✅ Status validation (only open/in_progress can be cancelled)
        - ✅ Status update to 'cancelled'
        - ✅ Comprehensive debug logging
        - ✅ Standardized response format
        - ✅ Cancellation audit trail
        
        PERMISSIONS: Customer (owner of request) or Admin
        DEBUG: All operations are tracked and logged
        """
        # 🔍 DEBUG: Log cancel request attempt
        logger.debug(f"🛑 DEBUG: Cancel service request {pk} attempted by user {request.user.id if request.user.is_authenticated else 'anonymous'} ({request.user.username if request.user.is_authenticated else 'anonymous'})")
        
        try:
            service_request = ServiceRequest.objects.get(pk=pk)
            logger.debug(f"📋 DEBUG: Service request found: {service_request.title} (Status: {service_request.status})")
        except ServiceRequest.DoesNotExist:
            logger.warning(f"❌ DEBUG: Service request {pk} not found")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Service request not found",
                    data={
                        'request_id': pk,
                        'error_type': 'not_found',
                        'requester_id': request.user.id if request.user.is_authenticated else None
                    },
                    status_code=404
                ),
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if the user is the owner of this request or admin
        if service_request.customer != request.user and not request.user.is_staff:
            logger.warning(f"🚫 DEBUG: Unauthorized cancel attempt - User {request.user.id} not owner of request {pk}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="You do not have permission to cancel this request",
                    data={
                        'request_id': pk,
                        'owner_id': service_request.customer.id,
                        'requester_id': request.user.id,
                        'error_type': 'permission_denied'
                    },
                    status_code=403
                ),
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Check if the request can be cancelled
        if service_request.status not in ['open', 'in_progress']:
            logger.warning(f"⚠️ DEBUG: Cannot cancel request {pk} with status '{service_request.status}'")
            return Response(
                StandardizedResponseHelper.error_response(
                    message=f"Cannot cancel a request with status '{service_request.status}'",
                    data={
                        'request_id': pk,
                        'current_status': service_request.status,
                        'cancellable_statuses': ['open', 'in_progress'],
                        'error_type': 'invalid_status_for_cancellation'
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Store original status for audit trail
            original_status = service_request.status
            cancellation_time = timezone.now()
            
            # Cancel the request
            service_request.status = 'cancelled'
            service_request.save()
            
            # 🎉 SUCCESS: Request cancelled successfully
            logger.info(f"✅ DEBUG: Service request {pk} cancelled successfully by user {request.user.id}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message="Service request cancelled successfully",
                    data={
                        'cancellation_details': {
                            'request_id': pk,
                            'request_title': service_request.title,
                            'previous_status': original_status,
                            'new_status': 'cancelled',
                            'cancelled_by': request.user.username,
                            'cancelled_at': cancellation_time.isoformat()
                        },
                        'request_info': {
                            'customer_id': str(service_request.customer.id),
                            'category': service_request.category.name,
                            'location': service_request.location,
                            'created_at': service_request.created_at.isoformat()
                        },
                        'cancellation_impact': {
                            'assigned_provider': str(service_request.assigned_provider.id) if service_request.assigned_provider else None,
                            'fulfilled_by_service': str(service_request.fulfilled_by_service.id) if service_request.fulfilled_by_service else None
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error cancelling service request {pk}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while cancelling the service request",
                    data={
                        'error_type': type(e).__name__,
                        'request_id': pk,
                        'attempted_by': request.user.id,
                        'attempted_at': timezone.now().isoformat()
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

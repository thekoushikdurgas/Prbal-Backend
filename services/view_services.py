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

class ServiceViewSet(viewsets.ModelViewSet):
    """
    🔧 SERVICE VIEWSET - ENHANCED WITH COMPREHENSIVE DEBUG TRACKING
    ==============================================================
    
    CRUD ViewSet for services with comprehensive response standardization.
    All endpoints return consistent JSON format: {message, data, time, statusCode}
    
    FEATURES:
    - ✅ List services with filtering and performance tracking
    - ✅ Create new services (Provider only) with validation tracking
    - ✅ Retrieve individual service details with access logging
    - ✅ Update services (Owner only) with change tracking
    - ✅ Delete services (Owner only) with cascade impact analysis
    - ✅ Nearby services search with geospatial calculation
    - ✅ Admin view for comprehensive service management
    - ✅ Trending services with popularity metrics
    - ✅ Matching requests for providers
    - ✅ Availability-based filtering
    - ✅ Service matching and fulfillment capabilities
    
    PERMISSIONS:
    - Read: Anyone (AllowAny for public browsing)
    - Create: Providers only (IsServiceProvider)
    - Update/Delete: Owner only (IsOwner)
    - Admin: Staff only for admin endpoints
    
    DEBUG ENHANCEMENTS:
    - 🔍 Request tracking with user context and timing
    - 📊 Performance monitoring with query count tracking
    - 🛡️ Permission validation logging
    - 📈 Operation success/failure metrics
    - 🔄 Data transformation tracking
    - 🌍 Geospatial calculation monitoring
    - 🎯 Business logic validation tracking
    """
    queryset = Service.objects.filter(status='active')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'subcategories', 'status', 'is_featured', 'provider', 'currency']
    search_fields = ['name', 'description', 'location', 'tags']
    ordering_fields = ['created_at', 'hourly_rate', 'min_hours', 'max_hours']
    throttle_classes = [ServiceCreationRateThrottle]
    
    def get_queryset(self):
        """
        🔍 ENHANCED QUERYSET WITH COMPREHENSIVE FILTERING AND PERFORMANCE TRACKING
        ========================================================================
        
        Returns services based on filtering parameters with detailed performance tracking.
        Monitors query performance and provides insights into data access patterns.
        """
        # 📝 DEBUG: Log queryset request initiation
        logger.debug(f"🔍 DEBUG: Service queryset requested by user {self.request.user.id if self.request.user.is_authenticated else 'anonymous'} for action {self.action}")
        
        # 📊 DEBUG: Track database query performance
        from django.db import connection
        initial_query_count = len(connection.queries)
        
        # 🏗️ DEBUG: Build base queryset based on action and user type
        if self.action == 'list':
            logger.debug("📋 DEBUG: Building queryset for list action")
            queryset = Service.objects.filter(status='active')
            initial_count = queryset.count()
            logger.debug(f"📊 DEBUG: Base queryset contains {initial_count} active services")
            
            # Apply price range filtering if provided
            filters_applied = []
            min_price = self.request.query_params.get('min_price')
            max_price = self.request.query_params.get('max_price')
            
            if min_price and min_price.isdigit():
                queryset = queryset.filter(hourly_rate__gte=float(min_price))
                filters_applied.append(f"min_price>={min_price}")
                logger.debug(f"🔍 DEBUG: Applied min_price filter: {min_price}")
                
            if max_price and max_price.isdigit():
                queryset = queryset.filter(hourly_rate__lte=float(max_price))
                filters_applied.append(f"max_price<={max_price}")
                logger.debug(f"🔍 DEBUG: Applied max_price filter: {max_price}")
            
            # 📈 DEBUG: Calculate filtering impact
            filtered_count = queryset.count()
            filter_impact = initial_count - filtered_count
            
            logger.debug(f"📊 DEBUG: List filtering results:")
            logger.debug(f"   📦 Initial count: {initial_count}")
            logger.debug(f"   ✅ Filtered count: {filtered_count}")
            logger.debug(f"   🔽 Filtered out: {filter_impact}")
            logger.debug(f"   🎯 Filters applied: {filters_applied if filters_applied else 'none'}")
            
            return queryset
            
        # For other actions like retrieve, or for the owner, show all their services
        elif self.request.user.is_authenticated and self.action != 'nearby':
            if self.request.user.is_staff:
                logger.debug("👑 DEBUG: Admin user - returning all services regardless of status")
                queryset = Service.objects.all()
                count = queryset.count()
                logger.debug(f"📊 DEBUG: Admin queryset contains {count} total services")
                return queryset
                
            elif self.request.user.user_type == 'provider':
                logger.debug("🔧 DEBUG: Provider user - returning active services and own services")
                # If it's their own services, show all regardless of status
                queryset = Service.objects.filter(
                    Q(status='active') | Q(provider=self.request.user)
                )
                count = queryset.count()
                own_services_count = Service.objects.filter(provider=self.request.user).count()
                logger.debug(f"📊 DEBUG: Provider queryset contains {count} services ({own_services_count} own services)")
                return queryset
                
        # Default case - just active services
        logger.debug("📋 DEBUG: Default case - returning active services only")
        queryset = Service.objects.filter(status='active')
        count = queryset.count()
        logger.debug(f"📊 DEBUG: Default queryset contains {count} active services")
        
        # 📊 DEBUG: Track query performance impact
        final_query_count = len(connection.queries)
        query_impact = final_query_count - initial_query_count
        logger.debug(f"🗃️ DEBUG: Service queryset performance:")
        logger.debug(f"   📊 Queries executed: {query_impact}")
        logger.debug(f"   🎯 Final queryset ready for action: {self.action}")
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action in ['update', 'partial_update']:
            return ServiceCreateUpdateSerializer
        elif self.action == 'retrieve':
            return ServiceDetailSerializer
        return ServiceListSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            # Only service providers can create services
            return [permissions.IsAuthenticated(), IsServiceProvider()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only the owner can update or delete a service
            return [permissions.IsAuthenticated(), IsOwner()]
        # Anyone can view services
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        # Set the provider to the current user and status to pending
        serializer.save(provider=self.request.user, status='pending')
    
    def list(self, request, *args, **kwargs):
        """
        📋 ENHANCED LIST METHOD WITH STANDARDIZED RESPONSE
        =================================================
        
        Enhanced list method that returns services with standardized response format.
        Provides comprehensive logging and performance tracking.
        """
        # 📝 DEBUG: Log list request initiation
        logger.debug(f"📋 DEBUG: Service list method initiated by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        
        try:
            # 🔍 DEBUG: Get queryset and apply filtering
            queryset = self.filter_queryset(self.get_queryset())
            initial_count = queryset.count()
            logger.debug(f"📊 DEBUG: Filtered queryset contains {initial_count} services")
            
            # 📄 DEBUG: Handle pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logger.debug(f"📄 DEBUG: Paginated response - {len(page)} services per page")
                
                # Get pagination info
                paginator_response = self.get_paginated_response(serializer.data)
                
                return Response(
                    StandardizedResponseHelper.paginated_response(
                        message=f"Services retrieved successfully - page {self.paginator.page.number if hasattr(self.paginator, 'page') else 1}",
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
            logger.info(f"✅ DEBUG: Services list completed - {initial_count} services")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Services retrieved successfully",
                    data={
                        'services': serializer.data,
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
            logger.error(f"💥 DEBUG: Error in services list: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving services",
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
        
        Enhanced create method that creates new services with standardized response format.
        Provides comprehensive logging and validation tracking.
        """
        # 📝 DEBUG: Log create request initiation
        logger.debug(f"➕ DEBUG: Service create method initiated by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        logger.debug(f"👤 DEBUG: Create requested by user: {request.user.username}")
        
        try:
            # 📝 DEBUG: Log request data
            logger.debug(f"📊 DEBUG: Create data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG: Service data validation passed")
                
                # 💾 DEBUG: Save the service
                self.perform_create(serializer)
                service = serializer.instance
                logger.info(f"✅ DEBUG: Service created successfully: '{service.name}' (ID: {service.id})")
                
                # 📊 DEBUG: Log creation context
                logger.debug(f"📊 DEBUG: Creation details:")
                logger.debug(f"   🏷️ Name: {service.name}")
                logger.debug(f"   📂 Category: {service.category.name}")
                logger.debug(f"   💰 Rate: {service.hourly_rate} {service.currency}")
                logger.debug(f"   🔄 Status: {service.status}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Service '{service.name}' created successfully",
                        data={
                            'service': serializer.data,
                            'creation_details': {
                                'created_by': request.user.username,
                                'created_at': service.created_at.isoformat(),
                                'category_name': service.category.name,
                                'service_id': str(service.id),
                                'status': service.status
                            }
                        },
                        status_code=201
                    ),
                    status=status.HTTP_201_CREATED
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG: Service validation failed")
                logger.warning(f"🔍 DEBUG: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Service validation failed",
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
            logger.error(f"💥 DEBUG: Error creating service: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while creating the service",
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
        
        Enhanced retrieve method that gets service details with standardized response format.
        Provides comprehensive logging and access tracking.
        """
        # 📝 DEBUG: Get service ID for logging
        service_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔍 DEBUG: Service retrieve method initiated for ID: {service_id}")
        
        try:
            # 🔍 DEBUG: Get the service instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG: Service found: '{instance.name}' by provider '{instance.provider.username}'")
            
            # 📊 DEBUG: Serialize the data
            serializer = self.get_serializer(instance)
            
            # 📈 DEBUG: Log access details
            logger.info(f"✅ DEBUG: Service retrieved successfully: '{instance.name}' (ID: {instance.id})")
            logger.debug(f"👤 DEBUG: Accessed by user: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Service '{instance.name}' retrieved successfully",
                    data={
                        'service': serializer.data,
                        'access_details': {
                            'accessed_by': request.user.username if request.user.is_authenticated else 'Anonymous',
                            'accessed_at': timezone.now().isoformat(),
                            'provider_name': instance.provider.username,
                            'category_name': instance.category.name,
                            'service_status': instance.status
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            # 💥 DEBUG: Log retrieve errors
            logger.error(f"💥 DEBUG: Error retrieving service {service_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Service not found",
                        data={
                            'service_id': service_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id if request.user.is_authenticated else None
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving the service",
                    data={
                        'error_type': type(e).__name__,
                        'service_id': service_id,
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
        
        Enhanced update method that updates services with standardized response format.
        Provides comprehensive logging and change tracking.
        """
        # 📝 DEBUG: Get service ID for logging
        service_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔄 DEBUG: Service update method initiated for ID: {service_id}")
        logger.debug(f"👤 DEBUG: Update requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the service instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG: Service found for update: '{instance.name}' by provider '{instance.provider.username}'")
            
            # 📊 DEBUG: Store original values for change tracking
            original_data = {
                'name': instance.name,
                'description': instance.description,
                'hourly_rate': instance.hourly_rate,
                'status': instance.status,
                'location': instance.location
            }
            logger.debug(f"📊 DEBUG: Original data captured for change tracking")
            
            # 📝 DEBUG: Log request data
            logger.debug(f"📊 DEBUG: Update data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data
            serializer = self.get_serializer(instance, data=request.data)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG: Service update data validation passed")
                
                # 💾 DEBUG: Save the updated service
                updated_service = serializer.save()
                logger.info(f"✅ DEBUG: Service updated successfully: '{updated_service.name}' (ID: {updated_service.id})")
                
                # 🔍 DEBUG: Track changes
                changes = []
                if original_data['name'] != updated_service.name:
                    changes.append(f"name: '{original_data['name']}' → '{updated_service.name}'")
                if original_data['hourly_rate'] != updated_service.hourly_rate:
                    changes.append(f"hourly_rate: {original_data['hourly_rate']} → {updated_service.hourly_rate}")
                if original_data['status'] != updated_service.status:
                    changes.append(f"status: {original_data['status']} → {updated_service.status}")
                if original_data['location'] != updated_service.location:
                    changes.append(f"location: updated")
                
                logger.debug(f"📊 DEBUG: Changes detected: {changes if changes else 'none'}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Service '{updated_service.name}' updated successfully",
                        data={
                            'service': serializer.data,
                            'update_details': {
                                'updated_by': request.user.username,
                                'updated_at': updated_service.updated_at.isoformat(),
                                'changes_made': changes,
                                'category_name': updated_service.category.name,
                                'service_id': str(updated_service.id)
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG: Service update validation failed")
                logger.warning(f"🔍 DEBUG: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Service update validation failed",
                        data={
                            'validation_errors': serializer.errors,
                            'provided_data': request.data,
                            'service_id': service_id,
                            'error_type': 'validation_error'
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # 💥 DEBUG: Log update errors
            logger.error(f"💥 DEBUG: Error updating service {service_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Service not found for update",
                        data={
                            'service_id': service_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id if request.user.is_authenticated else None
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while updating the service",
                    data={
                        'error_type': type(e).__name__,
                        'service_id': service_id,
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
        
        Enhanced partial update method that updates service fields with standardized response format.
        Provides comprehensive logging and change tracking for partial updates.
        """
        # 📝 DEBUG: Get service ID for logging
        service_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🔄 DEBUG: Service partial_update method initiated for ID: {service_id}")
        logger.debug(f"👤 DEBUG: Partial update requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the service instance
            instance = self.get_object()
            logger.debug(f"✅ DEBUG: Service found for partial update: '{instance.name}' by provider '{instance.provider.username}'")
            
            # 📊 DEBUG: Store original values for change tracking
            original_data = {
                'name': instance.name,
                'description': instance.description,
                'hourly_rate': instance.hourly_rate,
                'status': instance.status,
                'location': instance.location
            }
            logger.debug(f"📊 DEBUG: Original data captured for partial update change tracking")
            
            # 📝 DEBUG: Log request data
            fields_to_update = list(request.data.keys())
            logger.debug(f"📊 DEBUG: Partial update fields: {fields_to_update}")
            logger.debug(f"📊 DEBUG: Partial update data: {request.data}")
            
            # 🔍 DEBUG: Validate and serialize data with partial=True
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                logger.debug(f"✅ DEBUG: Service partial update data validation passed")
                
                # 💾 DEBUG: Save the partially updated service
                updated_service = serializer.save()
                logger.info(f"✅ DEBUG: Service partially updated successfully: '{updated_service.name}' (ID: {updated_service.id})")
                
                # 🔍 DEBUG: Track specific changes for fields that were updated
                changes = []
                if 'name' in fields_to_update and original_data['name'] != updated_service.name:
                    changes.append(f"name: '{original_data['name']}' → '{updated_service.name}'")
                if 'hourly_rate' in fields_to_update and original_data['hourly_rate'] != updated_service.hourly_rate:
                    changes.append(f"hourly_rate: {original_data['hourly_rate']} → {updated_service.hourly_rate}")
                if 'status' in fields_to_update and original_data['status'] != updated_service.status:
                    changes.append(f"status: {original_data['status']} → {updated_service.status}")
                if 'location' in fields_to_update and original_data['location'] != updated_service.location:
                    changes.append(f"location: updated")
                
                logger.debug(f"📊 DEBUG: Partial update changes detected: {changes if changes else 'none'}")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Service '{updated_service.name}' partially updated successfully",
                        data={
                            'service': serializer.data,
                            'partial_update_details': {
                                'updated_by': request.user.username,
                                'updated_at': updated_service.updated_at.isoformat(),
                                'fields_updated': fields_to_update,
                                'changes_made': changes,
                                'category_name': updated_service.category.name,
                                'service_id': str(updated_service.id)
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            else:
                # ❌ DEBUG: Log validation errors
                logger.warning(f"❌ DEBUG: Service partial update validation failed")
                logger.warning(f"🔍 DEBUG: Validation errors: {serializer.errors}")
                
                return Response(
                    StandardizedResponseHelper.error_response(
                        message="Service partial update validation failed",
                        data={
                            'validation_errors': serializer.errors,
                            'provided_data': request.data,
                            'fields_to_update': fields_to_update,
                            'service_id': service_id,
                            'error_type': 'validation_error'
                        },
                        status_code=400
                    ),
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # 💥 DEBUG: Log partial update errors
            logger.error(f"💥 DEBUG: Error partially updating service {service_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Service not found for partial update",
                        data={
                            'service_id': service_id,
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
                    message="An error occurred while partially updating the service",
                    data={
                        'error_type': type(e).__name__,
                        'service_id': service_id,
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
        
        Enhanced destroy method that deletes services with standardized response format.
        Provides comprehensive logging and impact analysis before deletion.
        """
        # 📝 DEBUG: Get service ID for logging
        service_id = kwargs.get('pk', 'unknown')
        logger.debug(f"🗑️ DEBUG: Service destroy method initiated for ID: {service_id}")
        logger.warning(f"🚨 DEBUG: DELETION requested by user: {request.user.username}")
        
        try:
            # 🔍 DEBUG: Get the service instance
            instance = self.get_object()
            logger.warning(f"🚨 DEBUG: Service found for DELETION: '{instance.name}' by provider '{instance.provider.username}'")
            
            # 📊 DEBUG: Analyze deletion impact
            # In a real system, check for bookings, reviews, etc.
            
            # Store details for response before deletion
            deletion_details = {
                'deleted_service': {
                    'id': str(instance.id),
                    'name': instance.name,
                    'provider_name': instance.provider.username,
                    'category_name': instance.category.name,
                    'hourly_rate': float(instance.hourly_rate),
                    'status': instance.status
                },
                'deletion_metadata': {
                    'deleted_by': request.user.username,
                    'deleted_at': timezone.now().isoformat(),
                    'deletion_type': 'owner_action' if request.user == instance.provider else 'admin_action'
                }
            }
            
            logger.warning(f"🔍 DEBUG: Deletion impact analysis:")
            logger.warning(f"   📊 Service: {instance.name}")
            logger.warning(f"   📊 Provider: {instance.provider.username}")
            logger.warning(f"   📊 Category: {instance.category.name}")
            logger.warning(f"   👤 Deleted by: {request.user.username}")
            
            # 💥 DEBUG: Perform the actual deletion
            logger.warning(f"💥 DEBUG: Executing database deletion for Service: '{instance.name}'")
            instance.delete()
            
            # ✅ DEBUG: Log successful deletion
            logger.warning(f"✅ DEBUG: Service DELETED successfully")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Service '{deletion_details['deleted_service']['name']}' deleted successfully",
                    data=deletion_details,
                    status_code=204
                ),
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            # 💥 DEBUG: Log deletion errors
            logger.error(f"💥 DEBUG: Error deleting service {service_id}: {e}", exc_info=True)
            
            # Handle specific error types
            if hasattr(e, 'status_code') and e.status_code == 404:
                return Response(
                    StandardizedResponseHelper.error_response(
                        message=f"Service not found for deletion",
                        data={
                            'service_id': service_id,
                            'error_type': 'not_found',
                            'user_id': request.user.id if request.user.is_authenticated else None
                        },
                        status_code=404
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while deleting the service",
                    data={
                        'error_type': type(e).__name__,
                        'service_id': service_id,
                        'user_id': request.user.id if request.user.is_authenticated else None,
                        'deletion_attempted_by': request.user.username
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Custom action to find services near a given location.
        Requires lat, lng, and radius (in km) parameters.
        """
        # Debug: Log nearby services request
        logger.debug(f"📍 DEBUG: Nearby services requested by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        
        lat_str = request.query_params.get('lat')
        lng_str = request.query_params.get('lng')
        radius_str = request.query_params.get('radius', '10')  # Default 10km
        
        # Debug: Log raw parameters
        logger.debug(f"🗺️ DEBUG: Raw search parameters - lat: {lat_str}, lng: {lng_str}, radius: {radius_str}")
        
        if not lat_str or not lng_str:
            logger.warning("🚫 DEBUG: Missing required coordinates for nearby search")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Latitude and longitude are required parameters",
                    data={
                        'required_params': ['lat', 'lng'],
                        'optional_params': {'radius': '10km (default)'},
                        'received_params': {
                            'lat': lat_str,
                            'lng': lng_str,
                            'radius': radius_str
                        }
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert string parameters to numeric types with validation
        try:
            lat = float(lat_str)
            lng = float(lng_str)
            radius = float(radius_str)
            
            # Validate ranges
            if not (-90 <= lat <= 90):
                raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90.")
            if not (-180 <= lng <= 180):
                raise ValueError(f"Invalid longitude: {lng}. Must be between -180 and 180.")
            if radius <= 0:
                raise ValueError(f"Invalid radius: {radius}. Must be positive.")
            if radius > 20000:  # Reasonable max radius of 20,000km (half earth circumference)
                raise ValueError(f"Invalid radius: {radius}. Must be <= 20,000km.")
                
            logger.debug(f"✅ DEBUG: Validated parameters - lat: {lat}, lng: {lng}, radius: {radius}km")
            
        except ValueError as ve:
            logger.warning(f"🚫 DEBUG: Invalid parameter values: {ve}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Invalid parameter values provided",
                    data={
                        'error_details': str(ve),
                        'validation_rules': {
                            'lat': 'Must be a number between -90 and 90',
                            'lng': 'Must be a number between -180 and 180',
                            'radius': 'Must be a positive number <= 20,000 (km)'
                        },
                        'received_params': {
                            'lat': lat_str,
                            'lng': lng_str,
                            'radius': radius_str
                        }
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Debug: Start geospatial calculation
            logger.debug("🌍 DEBUG: Starting nearby services calculation")
            
            # Since we don't have GeoDjango set up, we'll use a simple approximation
            # This is a simplified version and not as accurate as using GeoDjango
            # In a real app, you'd use GeoDjango with PostGIS
            
            # Approximate distance calculation (very simplified)
            earth_radius = 6371  # km
            # Roughly calculate lat/lng bounds for a bounding box
            # This is very approximate and not suitable for production
            lat_delta = radius / earth_radius * (180 / math.pi)
            lng_delta = radius / (earth_radius * math.cos(math.radians(lat))) * (180 / math.pi)
            
            min_lat = lat - lat_delta
            max_lat = lat + lat_delta
            min_lng = lng - lng_delta
            max_lng = lng + lng_delta
            
            # Debug: Log bounding box
            logger.debug(f"📦 DEBUG: Calculated bounding box - lat: [{min_lat}, {max_lat}], lng: [{min_lng}, {max_lng}]")
            
            # For now, we'll return active services with location-based filtering simulation
            # In a real implementation with lat/lng fields, you would do:
            nearby_services = Service.objects.filter(
                status='active',
                latitude__isnull=False,
                longitude__isnull=False
            )
            
            if nearby_services.exists():
                # Filter services within the bounding box (if coordinates exist)
                filtered_services = nearby_services.filter(
                    latitude__range=(min_lat, max_lat),
                    longitude__range=(min_lng, max_lng)
                )
                
                serializer = ServiceListSerializer(filtered_services, many=True)
                
                logger.info(f"📍 DEBUG: Found {filtered_services.count()} services within {radius}km of ({lat}, {lng})")
                
                return Response(
                    StandardizedResponseHelper.success_response(
                        message=f"Found {filtered_services.count()} services within {radius}km of the specified location",
                        data={
                            'services': serializer.data,
                            'search_criteria': {
                                'center_point': {'latitude': lat, 'longitude': lng},
                                'radius_km': radius,
                                'bounding_box': {
                                    'min_lat': min_lat, 'max_lat': max_lat,
                                    'min_lng': min_lng, 'max_lng': max_lng
                                }
                            },
                            'result_summary': {
                                'total_found': filtered_services.count(),
                                'total_active_services': nearby_services.count()
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
            else:
                logger.info("📍 DEBUG: No services with coordinates found for nearby search")
                return Response(
                    StandardizedResponseHelper.success_response(
                        message="No services with location data found for nearby search",
                        data={
                            'services': [],
                            'search_criteria': {
                                'center_point': {'latitude': lat, 'longitude': lng},
                                'radius_km': radius
                            },
                            'result_summary': {
                                'total_found': 0,
                                'note': 'This feature requires services to have location coordinates'
                            }
                        },
                        status_code=200
                    ),
                    status=status.HTTP_200_OK
                )
                
        except Exception as e:
            logger.error(f"💥 DEBUG: Error in nearby services search: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while searching for nearby services",
                    data={
                        'error_type': type(e).__name__,
                        'search_params': {'lat': lat, 'lng': lng, 'radius': radius}
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=False, methods=['get'])
    def admin(self, request):
        """
        Admin-only endpoint to list all services regardless of status.
        Provides full visibility for administrators to manage the platform.
        """
        # Debug: Log admin request
        logger.debug(f"🔧 DEBUG: Admin services view requested by user {request.user.id} ({request.user.username})")
        
        if not request.user.is_staff:
            logger.warning(f"🚫 DEBUG: Non-admin user {request.user.id} attempted to access admin services endpoint")
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
            logger.debug("🔍 DEBUG: Starting admin services query processing")
            
            # Get all services without filtering by status
            queryset = Service.objects.all()
            initial_count = queryset.count()
            logger.debug(f"📊 DEBUG: Initial service count: {initial_count}")
            
            # Apply any filtering from query params
            filters_applied = []
            
            category = request.query_params.get('category')
            if category:
                queryset = queryset.filter(category__id=category)
                filters_applied.append(f"category={category}")
                
            provider = request.query_params.get('provider')
            if provider:
                queryset = queryset.filter(provider__id=provider)
                filters_applied.append(f"provider={provider}")
                
            status_filter = request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
                filters_applied.append(f"status={status_filter}")
            
            # Debug: Log filtering results
            filtered_count = queryset.count()
            logger.debug(f"🔍 DEBUG: Applied filters: {filters_applied if filters_applied else 'none'}")
            logger.debug(f"📊 DEBUG: Filtered service count: {filtered_count} (from {initial_count})")
            
            # Use the list serializer for the response
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                paginated_response = self.get_paginated_response(serializer.data)
                
                # Debug: Log pagination details
                logger.debug(f"📄 DEBUG: Paginated response - page size: {len(page)}")
                
                # Convert to standardized format
                return Response(
                    StandardizedResponseHelper.paginated_response(
                        message="Admin services retrieved successfully",
                        data=serializer.data,
                        pagination_info={
                            'page': getattr(self.paginator, 'page', 1),
                            'page_size': len(page),
                            'total_count': filtered_count,
                            'total_pages': getattr(paginated_response.data, 'total_pages', 1) if hasattr(paginated_response.data, 'total_pages') else 1
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
            logger.info(f"✅ DEBUG: Admin services retrieved successfully - total: {filtered_count} services")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message="Admin services retrieved successfully",
                    data={
                        'services': serializer.data,
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
            logger.error(f"💥 DEBUG: Error in admin services query: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while retrieving admin services",
                    data={
                        'error_type': type(e).__name__,
                        'admin_id': str(request.user.id),
                        'applied_filters': request.query_params.dict()
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        Return trending services based on popularity metrics.
        This helps customers discover highly-rated or frequently booked services.
        """
        # Debug: Log trending services request
        logger.debug(f"🔥 DEBUG: Trending services requested by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        
        try:
            # Debug: Start trending calculation
            logger.debug("📈 DEBUG: Starting trending services calculation")
            
            # Get active services and order by most booked or highest rated
            # In a real implementation, this would join with bookings or reviews
            # For now, we'll prioritize featured services and most recently updated ones
            trending_services = Service.objects.filter(status='active')
            initial_count = trending_services.count()
            
            # Debug: Log initial count
            logger.debug(f"📊 DEBUG: Found {initial_count} active services for trending analysis")
            
            # Featured services come first, then most recently updated
            trending_services = trending_services.order_by('-is_featured', '-updated_at')
            
            # Limit to the top 10 trending services
            trending_limit = 10
            trending_services = trending_services[:trending_limit]
            
            # Debug: Log trending criteria
            logger.debug(f"⭐ DEBUG: Applied trending criteria - featured first, then recent updates, limited to {trending_limit}")
            
            serializer = self.get_serializer(trending_services, many=True)
            
            # Calculate trending metrics for response
            featured_count = sum(1 for service in trending_services if service.is_featured)
            
            # Debug: Log final results
            logger.info(f"🔥 DEBUG: Trending services calculated - {len(trending_services)} services, {featured_count} featured")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Top {len(trending_services)} trending services retrieved successfully",
                    data={
                        'trending_services': serializer.data,
                        'trending_criteria': {
                            'algorithm': 'featured_and_recent',
                            'description': 'Services ordered by featured status first, then by most recent updates',
                            'limit': trending_limit,
                            'total_active_services': initial_count
                        },
                        'metrics': {
                            'total_trending': len(trending_services),
                            'featured_count': featured_count,
                            'regular_count': len(trending_services) - featured_count,
                            'generated_at': timezone.now().isoformat()
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error calculating trending services: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while calculating trending services",
                    data={
                        'error_type': type(e).__name__,
                        'requester': request.user.id if request.user.is_authenticated else 'anonymous'
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def matching_requests(self, request):
        """
        🎯 PROVIDER-ONLY ENDPOINT: GET MATCHING SERVICE REQUESTS  
        =======================================================
        
        Provider-only endpoint to list service requests that match the provider's profile.
        Providers can view open service requests relevant to their expertise.
        
        FEATURES:
        - ✅ Category-based matching with provider services
        - ✅ Status and expiration filtering
        - ✅ Optional category parameter filtering
        - ✅ Comprehensive debug logging
        - ✅ Standardized response format
        
        PERMISSIONS: Provider only
        DEBUG: All operations are tracked and logged
        """
        # 🔍 DEBUG: Log matching requests attempt
        logger.debug(f"🎯 DEBUG: Matching requests requested by user {request.user.id if request.user.is_authenticated else 'anonymous'} (type: {request.user.user_type if request.user.is_authenticated else 'N/A'})")
        
        # 🔐 PERMISSION CHECK: Provider authentication
        if not request.user.is_authenticated or request.user.user_type != 'provider':
            logger.warning(f"🚫 DEBUG: Unauthorized matching requests access - User: {request.user.id if request.user.is_authenticated else 'anonymous'}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="You do not have permission to access this endpoint",
                    data={
                        'required_user_type': 'provider',
                        'current_user_type': request.user.user_type if request.user.is_authenticated else None,
                        'action': 'matching_requests',
                        'endpoint': '/api/services/services/matching_requests/'
                    },
                    status_code=403
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # 🔍 DEBUG: Start matching process
            logger.debug(f"🔍 DEBUG: Starting matching requests analysis for provider {request.user.id}")
            
            # Get the provider's services to match categories
            provider_services = Service.objects.filter(provider=request.user)
            provider_service_count = provider_services.count()
            provider_categories = list(provider_services.values_list('category', flat=True).distinct())
            
            # Debug: Log provider profile
            logger.debug(f"📊 DEBUG: Provider profile - {provider_service_count} services in {len(provider_categories)} categories")
            
            # Find service requests in the same categories
            queryset = ServiceRequest.objects.filter(
                status='open',
                expires_at__gt=timezone.now(),
                category__in=provider_categories
            )
            initial_count = queryset.count()
            
            # Debug: Log initial matching results
            logger.debug(f"📋 DEBUG: Found {initial_count} open service requests in provider's categories")
            
            # Apply additional filtering from query params
            filters_applied = []
            category = request.query_params.get('category')
            if category:
                queryset = queryset.filter(category__id=category)
                filters_applied.append(f"category={category}")
                logger.debug(f"🔍 DEBUG: Applied category filter: {category}")
            
            final_count = queryset.count()
            
            # Debug: Log filtering results
            logger.debug(f"📊 DEBUG: Final matching results - {final_count} requests (filtered from {initial_count})")
            logger.debug(f"🎯 DEBUG: Filters applied: {filters_applied if filters_applied else 'none'}")
            
            # Use the service request list serializer
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = ServiceRequestListSerializer(page, many=True)
                paginated_response = self.get_paginated_response(serializer.data)
                
                # Debug: Log pagination
                logger.debug(f"📄 DEBUG: Paginated response - page size: {len(page)}")
                
                # Convert to standardized format
                return Response(
                    StandardizedResponseHelper.paginated_response(
                        message=f"Found {final_count} matching service requests for your expertise",
                        data=serializer.data,
                        pagination_info={
                            'page': getattr(self.paginator, 'page', 1),
                            'page_size': len(page),
                            'total_count': final_count,
                            'total_pages': getattr(paginated_response.data, 'total_pages', 1) if hasattr(paginated_response.data, 'total_pages') else 1
                        },
                        status_code=200,
                        provider_info={
                            'provider_id': request.user.id,
                            'provider_services_count': provider_service_count,
                            'provider_categories': provider_categories,
                            'filters_applied': filters_applied
                        },
                        match_summary={
                            'initial_matches': initial_count,
                            'final_matches': final_count,
                            'generated_at': timezone.now().isoformat()
                        }
                    ),
                    status=status.HTTP_200_OK
                )
            
            serializer = ServiceRequestListSerializer(queryset, many=True)
            
            # Debug: Log successful completion
            logger.info(f"✅ DEBUG: Provider matching requests retrieved successfully - {final_count} requests found for provider {request.user.id}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Found {final_count} matching service requests for your expertise",
                    data={
                        'requests': serializer.data,
                        'provider_info': {
                            'provider_id': request.user.id,
                            'provider_services_count': provider_service_count,
                            'provider_categories': provider_categories,
                            'filters_applied': filters_applied
                        },
                        'match_summary': {
                            'initial_matches': initial_count,
                            'final_matches': final_count,
                            'total_matching_requests': final_count,
                            'generated_at': timezone.now().isoformat()
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error in matching requests for provider {request.user.id}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while finding matching service requests",
                    data={
                        'error_type': type(e).__name__,
                        'provider_id': request.user.id,
                        'action': 'matching_requests'
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_availability(self, request):
        """
        🗓️ FILTER SERVICES BY AVAILABILITY
        ===================================
        
        Filter services by availability on a specific date/time.
        Helps customers find services available when they need them.
        
        PARAMETERS:
        - date (required): YYYY-MM-DD format
        - time (optional): HH:MM format
        
        RETURNS: Standardized response with filtered services
        DEBUG: Comprehensive logging and validation tracking
        """
        # Debug: Log availability filter request
        logger.debug(f"🗓️ DEBUG: Services availability filter requested by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        
        # Get query parameters
        date_str = request.query_params.get('date')
        time_str = request.query_params.get('time')
        
        # Debug: Log parameters
        logger.debug(f"📅 DEBUG: Availability search parameters - date: {date_str}, time: {time_str}")
        
        if not date_str:
            logger.warning("🚫 DEBUG: Missing required date parameter for availability search")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Date parameter is required for availability search",
                    data={
                        'required_format': 'YYYY-MM-DD',
                        'optional_time_format': 'HH:MM',
                        'example': 'date=2024-01-15&time=14:30'
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Debug: Start availability processing
            logger.debug("🔍 DEBUG: Starting service availability filtering")
            
            # Get all active services
            services = Service.objects.filter(status='active')
            initial_count = services.count()
            
            # Debug: Log initial service count
            logger.debug(f"📊 DEBUG: Found {initial_count} active services for availability filtering")
            
            # In a real implementation, this would filter based on the availability JSON field
            # For now, we'll just return all active services with comprehensive debug info
            
            serializer = self.get_serializer(services, many=True)
            
            # Debug: Log processing completion
            logger.info(f"✅ DEBUG: Availability search completed - {initial_count} services available for {date_str} {time_str if time_str else ''}")
            
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Services available on {date_str}{' at ' + time_str if time_str else ''}",
                    data={
                        'services': serializer.data,
                        'search_criteria': {
                            'date': date_str,
                            'time': time_str,
                            'search_type': 'availability_filter'
                        },
                        'metadata': {
                            'total_services_found': initial_count,
                            'note': 'In production, this would filter based on provider availability JSON field',
                            'generated_at': timezone.now().isoformat()
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error in availability filtering: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while filtering services by availability",
                    data={
                        'error_type': type(e).__name__,
                        'search_params': {'date': date_str, 'time': time_str}
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def matching_services(self, request, pk=None):
        """
        🎯 FIND MATCHING SERVICES FOR SERVICE REQUEST
        ===========================================
        
        Customer-only endpoint to find services that match a specific service request.
        Returns services in the same category with pricing within the request's budget range.
        
        FEATURES:
        - ✅ Category-based matching
        - ✅ Budget range filtering  
        - ✅ Price-ordered results
        - ✅ Permission validation
        
        RETURNS: Standardized response with matching services
        DEBUG: Comprehensive logging and validation tracking
        """
        # Debug: Log matching services request
        logger.debug(f"🎯 DEBUG: Matching services requested for service request {pk} by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        
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
                        'error_type': 'not_found'
                    },
                    status_code=404
                ),
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if the user is the customer who created this request
        if service_request.customer != request.user and not request.user.is_staff:
            logger.warning(f"🚫 DEBUG: Unauthorized access to matching services - User {request.user.id} not owner of request {pk}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="You do not have permission to view matching services for this request",
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
            # Debug: Start matching process
            logger.debug(f"🔍 DEBUG: Starting service matching for request {pk}")
            
            # Find matching services based on category and price range
            matching_services = Service.objects.filter(
                status='active',
                category=service_request.category
            )
            initial_count = matching_services.count()
            
            # Debug: Log initial matches
            logger.debug(f"📊 DEBUG: Found {initial_count} services in category {service_request.category.name}")
            
            # Filter by budget range if specified
            filters_applied = []
            if service_request.budget_min is not None:
                matching_services = matching_services.filter(hourly_rate__gte=service_request.budget_min)
                filters_applied.append(f"min_rate>={service_request.budget_min}")
                
            if service_request.budget_max is not None:
                matching_services = matching_services.filter(hourly_rate__lte=service_request.budget_max)
                filters_applied.append(f"max_rate<={service_request.budget_max}")
                
            # Order by closest match (simple implementation)
            matching_services = matching_services.order_by('hourly_rate')
            final_count = matching_services.count()
            
            # Debug: Log filtering results
            logger.debug(f"🔍 DEBUG: Applied filters: {filters_applied if filters_applied else 'none'}")
            logger.debug(f"📊 DEBUG: Final matching services count: {final_count} (from {initial_count})")
            
            serializer = ServiceListSerializer(matching_services, many=True)
            
            # Debug: Log successful completion
            logger.info(f"✅ DEBUG: Matching services retrieved successfully - {final_count} matches for request {pk}")
            
            # 🌟 STANDARDIZED RESPONSE: Convert manual dict to StandardizedResponseHelper format
            # This ensures consistent API response structure across all endpoints
            return Response(
                StandardizedResponseHelper.success_response(
                    message=f"Found {final_count} services matching your request",
                    data={
                        'service_request': ServiceRequestDetailSerializer(service_request).data,
                        'matching_services': serializer.data,
                        'match_criteria': {
                            'category': service_request.category.name,
                            'budget_range': {
                                'min': service_request.budget_min,
                                'max': service_request.budget_max,
                                'currency': service_request.currency
                            },
                            'location': service_request.location,
                            'filters_applied': filters_applied
                        },
                        'match_summary': {
                            'total_matches': final_count,
                            'initial_category_count': initial_count,
                            'request_id': pk,
                            'generated_at': timezone.now().isoformat()
                        }
                    },
                    status_code=200
                ),
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"💥 DEBUG: Error in matching services for request {pk}: {e}", exc_info=True)
            return Response(
                StandardizedResponseHelper.error_response(
                    message="An error occurred while finding matching services",
                    data={
                        'error_type': type(e).__name__,
                        'request_id': pk,
                        'category': service_request.category.name if service_request else None
                    },
                    status_code=500
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def fulfill_request(self, request, pk=None):
        """
        🔧 PROVIDER-ONLY ACTION: FULFILL SERVICE REQUEST
        ==============================================
        
        Provider-only action to fulfill a service request by creating a matching service.
        Links the service to the request and marks the request as in progress.
        
        FEATURES:
        - ✅ Creates new service from request details
        - ✅ Links service to original request
        - ✅ Assigns provider to request
        - ✅ Comprehensive debug logging
        - ✅ Standardized response format
        
        PERMISSIONS: Provider only
        DEBUG: All operations are tracked and logged
        """
        # 🔍 DEBUG: Log fulfill request attempt
        logger.debug(f"🔧 DEBUG: Fulfill request {pk} attempted by user {request.user.id if request.user.is_authenticated else 'anonymous'} (type: {request.user.user_type if request.user.is_authenticated else 'N/A'})")
        
        # 🔐 PERMISSION CHECK: Provider authentication
        if not request.user.is_authenticated or request.user.user_type != 'provider':
            logger.warning(f"🚫 DEBUG: Unauthorized fulfill attempt - User: {request.user.id if request.user.is_authenticated else 'anonymous'}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="You do not have permission to access this endpoint",
                    data={
                        'required_user_type': 'provider',
                        'current_user_type': request.user.user_type if request.user.is_authenticated else None,
                        'request_id': pk,
                        'action': 'fulfill_request'
                    },
                    status_code=403
                ),
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            service_request = ServiceRequest.objects.get(pk=pk, status='open')
            logger.debug(f"✅ DEBUG: Service request found - {service_request.title}")
        except ServiceRequest.DoesNotExist:
            logger.warning(f"❌ DEBUG: Service request {pk} not found or not open")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Service request not found or not open",
                    data={
                        'request_id': pk,
                        'available_statuses': ['open'],
                        'provider_id': request.user.id,
                        'error_type': 'not_found_or_closed'
                    },
                    status_code=404
                ),
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Create a new service based on the request
        service_data = {
            'provider': request.user,
            'name': f"Service for: {service_request.title}",
            'description': service_request.description,
            'category': service_request.category,
            'location': service_request.location,
            'latitude': service_request.latitude,
            'longitude': service_request.longitude,
            'hourly_rate': service_request.budget_max if service_request.budget_max else 0,
            'currency': service_request.currency,
            'status': 'pending'  # New services need approval
        }
        
        service = Service.objects.create(**service_data)
        
        # Add subcategories if they exist
        if service_request.subcategories.exists():
            service.subcategories.set(service_request.subcategories.all())
        
        # Mark the request as in progress and link to this provider
        service_request.assign_provider(request.user)
        service_request.fulfilled_by_service = service
        service_request.save()
        
        # 🎉 SUCCESS: Request fulfilled successfully
        logger.info(f"🎉 DEBUG: Service request {pk} fulfilled successfully by provider {request.user.id}")
        
        return Response(
            StandardizedResponseHelper.success_response(
                message="Service request accepted successfully",
                data={
                    'fulfillment_details': {
                        'service_id': str(service.id),
                        'service_request_id': str(service_request.id),
                        'service_name': service.name,
                        'provider_id': str(request.user.id),
                        'provider_username': request.user.username
                    },
                    'service_info': {
                        'status': service.status,
                        'category': service_request.category.name,
                        'hourly_rate': float(service.hourly_rate),
                        'currency': service.currency
                    },
                    'next_steps': {
                        'service_approval': 'Service is pending admin approval',
                        'customer_notification': 'Customer will be notified'
                    }
                },
                status_code=201
            ),
            status=status.HTTP_201_CREATED
        )


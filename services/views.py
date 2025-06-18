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

# Create your views here.
class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    🗂️ SERVICE CATEGORY VIEWSET
    =========================
    
    CRUD ViewSet for service categories with comprehensive response standardization.
    All endpoints return consistent JSON format: {message, data, time, statusCode}
    
    FEATURES:
    - ✅ List categories with filtering
    - ✅ Retrieve individual category details  
    - ✅ Create new categories (Admin only)
    - ✅ Update existing categories (Admin only)
    - ✅ Delete categories (Admin only)
    - ✅ Statistics endpoint for admin analytics
    
    PERMISSIONS:
    - Read: Anyone (IsAuthenticatedOrReadOnly)
    - Write: Admin only (IsAdminUser)
    
    DEBUG: All responses are tracked and logged for monitoring
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    throttle_classes = [ServiceCategoryRateThrottle]
    
    def get_queryset(self):
        """
        🔍 Enhanced queryset with filtering and debug tracking
        Returns categories based on active_only parameter
        """
        # Debug: Log queryset request
        logger.debug(f"🗂️ DEBUG: ServiceCategory queryset requested by user {self.request.user.id if self.request.user.is_authenticated else 'anonymous'}")
        
        queryset = ServiceCategory.objects.all()
        initial_count = queryset.count()
        
        # Apply active_only filter if provided
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)
            logger.debug(f"🔍 DEBUG: Applied active_only=true filter")
        elif active_only and active_only.lower() == 'false':
            queryset = queryset.filter(is_active=False)
            logger.debug(f"🔍 DEBUG: Applied active_only=false filter")
        
        filtered_count = queryset.count()
        logger.debug(f"📊 DEBUG: Category queryset - Initial: {initial_count}, Filtered: {filtered_count}")
        
        return queryset
    
    def get_permissions(self):
        """
        🔐 Dynamic permission handling with debug logging
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'statistics']:
            logger.debug(f"🔐 DEBUG: Admin permission required for action: {self.action}")
            return [permissions.IsAdminUser()]
        
        logger.debug(f"🔓 DEBUG: Public access allowed for action: {self.action}")
        return [permissions.IsAuthenticatedOrReadOnly()]
        
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


class ServiceSubCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service subcategories - allows listing, retrieving, creating, updating, and deleting subcategories.
    Only authenticated staff users can create, update, or delete subcategories.
    """
    queryset = ServiceSubCategory.objects.filter(is_active=True)
    serializer_class = ServiceSubCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'category']
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'sort_order', 'category__name', 'created_at']
    throttle_classes = [ServiceSubCategoryRateThrottle]
    
    def get_queryset(self):
        queryset = ServiceSubCategory.objects.all()
        
        # Apply active_only filter if provided
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        elif active_only and active_only.lower() == 'false':
            queryset = queryset.filter(is_active=False)
            
        # Apply category filter if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]

class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for services - allows listing, retrieving, creating, updating, and deleting services.
    Only service providers can create services, and only the owner can update or delete them.
    """
    queryset = Service.objects.filter(status='active')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'subcategories', 'status', 'is_featured', 'provider', 'currency']
    search_fields = ['name', 'description', 'location', 'tags']
    ordering_fields = ['created_at', 'hourly_rate', 'min_hours', 'max_hours']
    
    def get_queryset(self):
        # For list view, only show active services
        if self.action == 'list':
            queryset = Service.objects.filter(status='active')
            
            # Apply price range filtering if provided
            min_price = self.request.query_params.get('min_price')
            max_price = self.request.query_params.get('max_price')
            
            if min_price and min_price.isdigit():
                queryset = queryset.filter(hourly_rate__gte=float(min_price))
                
            if max_price and max_price.isdigit():
                queryset = queryset.filter(hourly_rate__lte=float(max_price))
                
            return queryset
        # For other actions like retrieve, or for the owner, show all their services
        elif self.request.user.is_authenticated and self.action != 'nearby':
            if self.request.user.is_staff:
                return Service.objects.all()
            elif self.request.user.user_type == 'provider':
                # If it's their own services, show all regardless of status
                return Service.objects.filter(
                    Q(status='active') | Q(provider=self.request.user)
                )
        # Default case - just active services
        return Service.objects.filter(status='active')
    
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
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Custom action to find services near a given location.
        Requires lat, lng, and radius (in km) parameters.
        """
        # Debug: Log nearby services request
        logger.debug(f"📍 DEBUG: Nearby services requested by user {request.user.id if request.user.is_authenticated else 'anonymous'}")
        
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', 10)  # Default 10km
        
        # Debug: Log parameters
        logger.debug(f"🗺️ DEBUG: Search parameters - lat: {lat}, lng: {lng}, radius: {radius}")
        
        if not lat or not lng:
            logger.warning("🚫 DEBUG: Missing required coordinates for nearby search")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Latitude and longitude are required parameters",
                    data={
                        'required_params': ['lat', 'lng'],
                        'optional_params': {'radius': '10km (default)'},
                        'received_params': {
                            'lat': lat,
                            'lng': lng,
                            'radius': radius
                        }
                    },
                    status_code=400
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
            
            # Debug: Log coordinate validation success
            logger.debug(f"✅ DEBUG: Coordinates validated - lat: {lat}, lng: {lng}, radius: {radius}km")
            
        except ValueError as e:
            logger.warning(f"❌ DEBUG: Invalid coordinate format: {e}")
            return Response(
                StandardizedResponseHelper.error_response(
                    message="Invalid coordinate or radius format",
                    data={
                        'error_details': 'Coordinates must be valid numbers',
                        'provided_values': {
                            'lat': request.query_params.get('lat'),
                            'lng': request.query_params.get('lng'),
                            'radius': request.query_params.get('radius')
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
        Provider-only endpoint to list service requests that match the provider's profile.
        Providers can view open service requests relevant to their expertise.
        """
        if not request.user.is_authenticated or request.user.user_type != 'provider':
            return Response(
                {"error": "You do not have permission to access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Get the provider's services to match categories
        provider_services = Service.objects.filter(provider=request.user)
        provider_categories = provider_services.values_list('category', flat=True).distinct()
        
        # Find service requests in the same categories
        queryset = ServiceRequest.objects.filter(
            status='open',
            expires_at__gt=timezone.now(),
            category__in=provider_categories
        )
        
        # Apply any filtering from query params
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__id=category)
            
        # Use the service request list serializer
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ServiceRequestListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ServiceRequestListSerializer(queryset, many=True)
        
        # Debug: Log response preparation
        logger.info(f"✅ DEBUG: Provider matching requests retrieved - {queryset.count()} requests found for provider {request.user.id}")
        
        return Response(
            StandardizedResponseHelper.success_response(
                message=f"Found {queryset.count()} matching service requests for your expertise",
                data={
                    'requests': serializer.data,
                    'provider_info': {
                        'provider_id': request.user.id,
                        'provider_categories': list(provider_categories),
                        'total_matching_requests': queryset.count(),
                        'generated_at': timezone.now().isoformat()
                    }
                },
                status_code=200
            ),
            status=status.HTTP_200_OK
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
                
                # Convert to standardized format
                return Response(
                    StandardizedResponseHelper.paginated_response(
                        message=f"Customer service requests retrieved successfully",
                        data=serializer.data,
                        pagination_info={
                            'page': getattr(self.paginator, 'page', 1),
                            'page_size': len(page),
                            'total_count': filtered_count,
                            'total_pages': getattr(paginated_response.data, 'total_pages', 1) if hasattr(paginated_response.data, 'total_pages') else 1
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
                
                # Convert to standardized format
                return Response(
                    StandardizedResponseHelper.paginated_response(
                        message="Admin service requests retrieved successfully",
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

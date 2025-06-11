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

User = get_user_model()

# Create your views here.
class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service categories - allows listing, retrieving, creating, updating, and deleting categories.
    Only authenticated staff users can create, update, or delete categories.
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
        queryset = ServiceCategory.objects.all()
        
        # Apply active_only filter if provided
        active_only = self.request.query_params.get('active_only')
        if active_only and active_only.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        elif active_only and active_only.lower() == 'false':
            queryset = queryset.filter(is_active=False)
            
        return queryset
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'statistics']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]
        
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Admin endpoint to get statistics about service distribution by category.
        Provides insights into which categories are most popular among providers and customers.
        """
        # Check if the user is an admin
        if not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Get all active categories
        categories = ServiceCategory.objects.filter(is_active=True)
        
        # Prepare statistics
        category_stats = []
        for category in categories:
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
        
        return Response({
            'total_categories': len(category_stats),
            'total_services': Service.objects.count(),
            'total_requests': ServiceRequest.objects.count(),
            'category_statistics': category_stats
        })


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
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', 10)  # Default 10km
        
        if not lat or not lng:
            return Response(
                {"error": "Latitude and longitude are required parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
        except ValueError:
            return Response(
                {"error": "Invalid coordinate or radius format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        # For a real implementation, you would need to store lat/lng in your Service model
        # and use a proper geospatial query. This is a placeholder for demonstration
        
        # In a real implementation with lat/lng fields, you would do:
        # nearby_services = Service.objects.filter(
        #     status='active',
        #     latitude__range=(min_lat, max_lat),
        #     longitude__range=(min_lng, max_lng)
        # )
        
        # Since we don't have those fields, we'll just return a message
        return Response(
            {"message": "This is a placeholder for the nearby services feature. In a real implementation, this would return services within a " + str(radius) + "km radius of the provided coordinates."},
            status=status.HTTP_200_OK
        )
        
    @action(detail=False, methods=['get'])
    def admin(self, request):
        """
        Admin-only endpoint to list all services regardless of status.
        Provides full visibility for administrators to manage the platform.
        """
        if not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all services without filtering by status
        queryset = Service.objects.all()
        
        # Apply any filtering from query params
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__id=category)
            
        provider = request.query_params.get('provider')
        if provider:
            queryset = queryset.filter(provider__id=provider)
            
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Use the list serializer for the response
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        Return trending services based on popularity metrics.
        This helps customers discover highly-rated or frequently booked services.
        """
        # Get active services and order by most booked or highest rated
        # In a real implementation, this would join with bookings or reviews
        # For now, we'll prioritize featured services and most recently updated ones
        trending_services = Service.objects.filter(status='active')
        
        # Featured services come first
        trending_services = trending_services.order_by('-is_featured', '-updated_at')
        
        # Limit to the top 10 trending services
        trending_services = trending_services[:10]
        
        serializer = self.get_serializer(trending_services, many=True)
        return Response(serializer.data)
    
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
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def by_availability(self, request):
        """
        Filter services by availability on a specific date/time.
        Helps customers find services available when they need them.
        """
        # Get query parameters
        date_str = request.query_params.get('date')
        time_str = request.query_params.get('time')
        
        if not date_str:
            return Response(
                {"error": "Date parameter is required (format: YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get all active services
        services = Service.objects.filter(status='active')
        
        # In a real implementation, this would filter based on the availability JSON field
        # For now, we'll just return all active services with a note
        
        serializer = self.get_serializer(services, many=True)
        return Response({
            "message": f"In a production environment, this would filter services available on {date_str} {time_str if time_str else ''}",
            "services": serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def matching_services(self, request, pk=None):
        """
        Customer-only endpoint to find services that match a specific service request.
        Returns services in the same category with pricing within the request's budget range.
        """
        try:
            service_request = ServiceRequest.objects.get(pk=pk)
        except ServiceRequest.DoesNotExist:
            return Response(
                {"error": "Service request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if the user is the customer who created this request
        if service_request.customer != request.user and not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to view matching services for this request"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Find matching services based on category and price range
        matching_services = Service.objects.filter(
            status='active',
            category=service_request.category
        )
        
        # Filter by budget range if specified
        if service_request.budget_min is not None:
            matching_services = matching_services.filter(hourly_rate__gte=service_request.budget_min)
            
        if service_request.budget_max is not None:
            matching_services = matching_services.filter(hourly_rate__lte=service_request.budget_max)
            
        # Order by closest match (simple implementation)
        matching_services = matching_services.order_by('hourly_rate')
        
        serializer = ServiceListSerializer(matching_services, many=True)
        return Response({
            "request": ServiceRequestDetailSerializer(service_request).data,
            "matching_services": serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def fulfill_request(self, request, pk=None):
        """
        Provider-only action to fulfill a service request by creating a matching service.
        Links the service to the request and marks the request as in progress.
        """
        if not request.user.is_authenticated or request.user.user_type != 'provider':
            return Response(
                {"error": "You do not have permission to access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            service_request = ServiceRequest.objects.get(pk=pk, status='open')
        except ServiceRequest.DoesNotExist:
            return Response(
                {"error": "Service request not found or not open"},
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
        
        return Response(
            {
                "message": "Service request accepted successfully",
                "service_id": service.id,
                "service_request_id": service_request.id
            },
            status=status.HTTP_201_CREATED
        )


class ServiceRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service requests - allows customers to request services they need.
    Providers can browse and fulfill these requests.
    """
    queryset = ServiceRequest.objects.filter(status='open', expires_at__gt=timezone.now())
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status', 'urgency', 'is_featured', 'customer']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'expires_at', 'budget_max']
    
    def get_queryset(self):
        # For list view, only show open, non-expired requests
        if self.action == 'list':
            return ServiceRequest.objects.filter(
                status='open',
                expires_at__gt=timezone.now()
            )
        # For other actions like retrieve, or for the owner, show all their requests
        elif self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return ServiceRequest.objects.all()
            elif self.request.user.user_type == 'customer':
                # If it's their own requests, show all regardless of status
                return ServiceRequest.objects.filter(
                    Q(status='open', expires_at__gt=timezone.now()) | 
                    Q(customer=self.request.user)
                )
            elif self.request.user.user_type == 'provider':
                # Show open requests and ones assigned to this provider
                return ServiceRequest.objects.filter(
                    Q(status='open', expires_at__gt=timezone.now()) | 
                    Q(assigned_provider=self.request.user)
                )
        # Default case - just open, non-expired requests
        return ServiceRequest.objects.filter(status='open', expires_at__gt=timezone.now())
    
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
        """
        if not request.user.is_authenticated or request.user.user_type != 'customer':
            return Response(
                {"error": "You do not have permission to access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        queryset = ServiceRequest.objects.filter(customer=request.user)
        
        # Apply any filtering from query params
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Use the service request list serializer
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'])
    def admin(self, request):
        """
        Admin-only endpoint to list all service requests regardless of status.
        Provides full visibility for administrators to manage the platform.
        """
        if not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all service requests without filtering by status
        queryset = ServiceRequest.objects.all()
        
        # Apply any filtering from query params
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__id=category)
            
        customer = request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(customer__id=customer)
            
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Use the list serializer for the response
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
    @action(detail=True, methods=['get'])
    def recommended_providers(self, request, pk=None):
        """
        Customer endpoint to get recommended providers for a specific service request.
        Returns providers who offer services in the same category and have good ratings.
        """
        try:
            service_request = ServiceRequest.objects.get(pk=pk)
        except ServiceRequest.DoesNotExist:
            return Response(
                {"error": "Service request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if the user is authorized to view recommendations
        if service_request.customer != request.user and not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to view provider recommendations for this request"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Find providers who offer services in the same category
        from users.serializers import PublicUserProfileSerializer
        
        # Get providers with active services in this category
        providers = User.objects.filter(
            user_type='provider',
            services__category=service_request.category,
            services__status='active'
        ).distinct()
        
        # In a real implementation, we would also sort by rating, distance, etc.
        serializer = PublicUserProfileSerializer(providers, many=True)
        
        return Response({
            "request": ServiceRequestDetailSerializer(service_request).data,
            "recommended_providers": serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def batch_expire(self, request):
        """
        Admin-only action to expire all service requests that have passed their expiration date.
        This helps keep the marketplace clean and up-to-date.
        """
        if not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to perform this action"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Find all expired but still open requests
        expired_requests = ServiceRequest.objects.filter(
            status='open',
            expires_at__lt=timezone.now()
        )
        
        count = expired_requests.count()
        
        # Mark them all as expired
        for req in expired_requests:
            req.mark_as_expired()
        
        return Response({
            "message": f"Successfully expired {count} service requests",
            "expired_count": count
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Customer-only action to cancel their service request.
        """
        try:
            service_request = ServiceRequest.objects.get(pk=pk)
        except ServiceRequest.DoesNotExist:
            return Response(
                {"error": "Service request not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if the user is the owner of this request
        if service_request.customer != request.user and not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to cancel this request"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Check if the request can be cancelled
        if service_request.status not in ['open', 'in_progress']:
            return Response(
                {"error": f"Cannot cancel a request with status '{service_request.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Cancel the request
        service_request.status = 'cancelled'
        service_request.save()
        
        return Response(
            {"message": "Service request cancelled successfully"},
            status=status.HTTP_200_OK
        )

from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import ProductCategory, Product
from .serializers import (
    ProductCategorySerializer,
    ProductListSerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer
)
from services.permissions import IsServiceProvider, IsOwner

class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product categories - allows listing, retrieving, creating, updating, and deleting categories.
    Only authenticated staff users can create, update, or delete categories.
    """
    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticatedOrReadOnly()]

class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for products - allows listing, retrieving, creating, updating, and deleting products.
    Only service providers can create products, and only the owner can update or delete them.
    """
    queryset = Product.objects.filter(status='active')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'related_service_category', 'status', 'is_featured', 
                        'seller', 'product_type']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'price']
    
    def get_queryset(self):
        # For list view, only show active products
        if self.action == 'list':
            return Product.objects.filter(status='active')
        # For other actions like retrieve, or for the owner, show all their products
        elif self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return Product.objects.all()
            elif self.request.user.user_type == 'provider':
                # If it's their own products, show all regardless of status
                return Product.objects.filter(
                    Q(status='active') | Q(seller=self.request.user)
                )
        # Default case - just active products
        return Product.objects.filter(status='active')
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action in ['update', 'partial_update']:
            return ProductCreateUpdateSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            # Only service providers can create products
            return [permissions.IsAuthenticated(), IsServiceProvider()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only the owner can update or delete a product
            return [permissions.IsAuthenticated(), IsOwner()]
        # Anyone can view products
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        # Set the seller to the current user and status to pending
        serializer.save(seller=self.request.user, status='pending')

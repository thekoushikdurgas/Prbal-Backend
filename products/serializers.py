from rest_framework import serializers
from .models import ProductCategory, Product
from services.serializers import Base64ImageField
from users.serializers import PublicUserProfileSerializer
from services.models import ServiceCategory

class ProductCategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories"""
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'description', 'icon', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ServiceCategoryReferenceSerializer(serializers.ModelSerializer):
    """Simple serializer for service category references"""
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name']
        read_only_fields = fields

class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for listing products with seller details"""
    seller = PublicUserProfileSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    related_service_category_name = serializers.CharField(
        source='related_service_category.name', 
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'category', 'category_name', 
            'related_service_category', 'related_service_category_name',
            'name', 'description', 'price', 'discount_price', 
            'product_type', 'stock_quantity', 'images',
            'status', 'is_featured', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'seller', 'status', 'is_featured', 'created_at', 'updated_at']

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products"""
    # For handling base64 images if needed
    # main_image = Base64ImageField(required=False)
    
    class Meta:
        model = Product
        fields = [
            'id', 'category', 'related_service_category',
            'name', 'description', 'price', 'discount_price',
            'product_type', 'stock_quantity', 'images',
            'features', 'specifications'
        ]
        read_only_fields = ['id']
    
    def validate_category(self, value):
        """Ensure the category is active"""
        if not value.is_active:
            raise serializers.ValidationError("This category is not active.")
        return value
    
    def validate(self, data):
        """Additional validation"""
        # Ensure discount price is less than regular price if provided
        if 'discount_price' in data and data['discount_price'] is not None:
            if data['discount_price'] >= data['price']:
                raise serializers.ValidationError(
                    {"discount_price": "Discount price must be less than regular price."}
                )
        return data

class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed product view"""
    seller = PublicUserProfileSerializer(read_only=True)
    category = ProductCategorySerializer(read_only=True)
    related_service_category = ServiceCategoryReferenceSerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'category', 'related_service_category',
            'name', 'description', 'price', 'discount_price',
            'product_type', 'stock_quantity', 'images',
            'features', 'specifications', 'status', 'is_featured',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

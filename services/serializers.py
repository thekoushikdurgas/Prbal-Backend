from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ServiceCategory, ServiceSubCategory, Service, ServiceImage, ServiceRequest
from users.serializers import PublicUserProfileSerializer
import base64
import uuid
from django.core.files.base import ContentFile

User = get_user_model()

class ServiceCategorySerializer(serializers.ModelSerializer):
    """Serializer for service categories"""
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'icon', 'icon_url', 'sort_order', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceSubCategorySerializer(serializers.ModelSerializer):
    """Serializer for service subcategories"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ServiceSubCategory
        fields = ['id', 'category', 'category_name', 'name', 'description', 'icon', 'icon_url', 'sort_order', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ServiceListSerializer(serializers.ModelSerializer):
    """Serializer for listing services with provider details"""
    provider = PublicUserProfileSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategories = ServiceSubCategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'provider', 'category', 'category_name', 'subcategories', 'title', 
            'description', 'price', 'location', 'image', 'status', 
            'is_featured', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'provider', 'status', 'is_featured', 'created_at', 'updated_at']

class Base64ImageField(serializers.ImageField):
    """Custom field for handling base64 encoded images"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            # Base64 encoded image - decode
            format, imgstr = data.split(';base64,') 
            ext = format.split('/')[-1] 
            
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f"{uuid.uuid4()}.{ext}"
            )
            
        return super().to_internal_value(data)

class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating services"""
    image = Base64ImageField(required=False)
    
    class Meta:
        model = Service
        fields = [
            'id', 'category', 'title', 'description', 'price', 
            'location', 'image'
        ]
        read_only_fields = ['id']
    
    def validate_category(self, value):
        """Ensure the category is active"""
        if not value.is_active:
            raise serializers.ValidationError("This category is not active.")
        return value

class ServiceImageSerializer(serializers.ModelSerializer):
    """Serializer for service images"""
    image = Base64ImageField(required=False)
    
    class Meta:
        model = ServiceImage
        fields = ['id', 'image', 'description', 'order']
        read_only_fields = ['id']

class ServiceDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed service view"""
    provider = PublicUserProfileSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    subcategories = ServiceSubCategorySerializer(many=True, read_only=True)
    service_images = ServiceImageSerializer(many=True, read_only=True)
    tags = serializers.JSONField(required=False)
    pricing_options = serializers.JSONField(required=False)
    availability = serializers.JSONField(required=False)
    required_tools = serializers.JSONField(required=False)
    
    class Meta:
        model = Service
        fields = [
            'id', 'provider', 'name', 'description',
            'category', 'subcategories', 'tags',
            'hourly_rate', 'pricing_options', 'currency', 'min_hours', 'max_hours',
            'availability', 'location', 'latitude', 'longitude',
            'required_tools', 'status', 'is_featured',
            'service_images', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
        
    # For backward compatibility
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['title'] = instance.name
        ret['price'] = instance.hourly_rate
        if instance.service_images.exists():
            ret['image'] = instance.service_images.first().image.url
        return ret

class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for creating and updating services"""
    images = ServiceImageSerializer(many=True, required=False)
    tags = serializers.JSONField(required=False)
    pricing_options = serializers.JSONField(required=False)
    availability = serializers.JSONField(required=False)
    required_tools = serializers.JSONField(required=False)
    
    class Meta:
        model = Service
        fields = [
            'id', 'category', 'subcategories', 'name', 'description',
            'hourly_rate', 'pricing_options', 'currency', 'min_hours', 'max_hours',
            'availability', 'location', 'latitude', 'longitude', 
            'required_tools', 'tags', 'images'
        ]
        read_only_fields = ['id']
    
    def validate_category(self, value):
        """Ensure the category is active"""
        if not value.is_active:
            raise serializers.ValidationError("This category is not active.")
        return value
    
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        service = Service.objects.create(**validated_data)
        
        # Process images if any
        for image_data in images_data:
            ServiceImage.objects.create(service=service, **image_data)
            
        return service
    
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', [])
        
        # Update the service instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle image updates if provided
        if images_data:
            # Option: Replace all images
            instance.service_images.all().delete()
            for image_data in images_data:
                ServiceImage.objects.create(service=instance, **image_data)
                
        return instance

# Service Request Serializers
class ServiceRequestListSerializer(serializers.ModelSerializer):
    """Serializer for listing service requests"""
    customer = PublicUserProfileSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'customer', 'title', 'description', 
            'category', 'category_name', 'status', 'status_display',
            'urgency', 'urgency_display', 'location', 'budget_min', 'budget_max',
            'currency', 'is_featured', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'customer', 'status', 'is_featured', 'created_at', 'expires_at']

class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating service requests"""
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'title', 'description', 'category', 'subcategories',
            'budget_min', 'budget_max', 'currency', 'urgency', 'requested_date_time',
            'location', 'latitude', 'longitude', 'requirements'
        ]
        read_only_fields = ['id']
    
    def validate_category(self, value):
        """Ensure the category is active"""
        if not value.is_active:
            raise serializers.ValidationError("This category is not active.")
        return value
        
class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed service request view"""
    customer = PublicUserProfileSerializer(read_only=True)
    assigned_provider = PublicUserProfileSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    subcategories = ServiceSubCategorySerializer(many=True, read_only=True)
    fulfilled_by_service = ServiceDetailSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    urgency_display = serializers.CharField(source='get_urgency_display', read_only=True)
    requirements = serializers.JSONField(required=False)
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'customer', 'title', 'description',
            'category', 'subcategories', 
            'budget_min', 'budget_max', 'currency', 'urgency', 'urgency_display',
            'requested_date_time', 'location', 'latitude', 'longitude',
            'status', 'status_display', 'is_featured', 'expires_at',
            'assigned_provider', 'fulfilled_by_service', 'requirements',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

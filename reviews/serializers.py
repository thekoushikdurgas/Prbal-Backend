from rest_framework import serializers
from .models import Review, ReviewImage
from users.serializers import PublicUserProfileSerializer
from services.serializers import ServiceDetailSerializer as ServiceSerializer
from bookings.models import Booking
from django.utils import timezone
import base64
import uuid
from django.core.files.base import ContentFile

class Base64ImageField(serializers.ImageField):
    """Custom field for handling base64 encoded images"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:'):
            # Base64 encoded file - decode
            format, filestr = data.split(';base64,') 
            ext = format.split('/')[-1] 
            
            data = ContentFile(
                base64.b64decode(filestr),
                name=f"{uuid.uuid4()}.{ext}"
            )
            
        return super().to_internal_value(data)

class ReviewImageSerializer(serializers.ModelSerializer):
    """Serializer for review images"""
    image = Base64ImageField()
    
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'caption', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer for listing reviews"""
    reviewer_name = serializers.CharField(source='client.get_full_name', read_only=True)
    reviewer_profile_pic = serializers.ImageField(source='client.profile_picture', read_only=True)
    service_title = serializers.CharField(source='service.title', read_only=True)
    has_provider_response = serializers.SerializerMethodField()
    images_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'booking', 'service', 'service_title', 'client', 
            'reviewer_name', 'reviewer_profile_pic', 'provider', 'rating', 
            'comment', 'has_provider_response', 'images_count', 'created_at'
        ]
        read_only_fields = fields
    
    def get_has_provider_response(self, obj):
        return bool(obj.provider_response)
    
    def get_images_count(self, obj):
        return obj.images.count()

class ReviewDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed review view"""
    client = PublicUserProfileSerializer(read_only=True)
    provider = PublicUserProfileSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'booking', 'service', 'client', 'provider', 'rating',
            'comment', 'provider_response', 'provider_response_date',
            'is_public', 'images', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new review with images"""
    images = serializers.ListField(
        child=Base64ImageField(),
        required=False,
        write_only=True
    )
    image_captions = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Review
        fields = [
            'booking', 'rating', 'comment', 'images', 'image_captions', 'is_public'
        ]
    
    def validate_booking(self, value):
        user = self.context['request'].user
        
        # Check if the booking exists and belongs to the user
        try:
            booking = Booking.objects.get(id=value.id)
            
            # Check if user is the customer of the booking
            if booking.customer != user:
                raise serializers.ValidationError(
                    "You can only review bookings where you are the customer."
                )
            
            # Check if booking is completed
            if booking.status != 'completed':
                raise serializers.ValidationError(
                    "You can only review completed bookings."
                )
            
            # Check if review already exists for this booking
            if Review.objects.filter(booking=booking).exists():
                raise serializers.ValidationError(
                    "You have already reviewed this booking."
                )
                
            return value
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")
    
    def validate(self, data):
        # Validate that if images are provided, captions have the same length
        images = data.get('images', [])
        captions = data.get('image_captions', [])
        
        if images and captions and len(images) != len(captions):
            raise serializers.ValidationError(
                "The number of image captions must match the number of images."
            )
            
        return data
    
    def create(self, validated_data):
        # Extract images and captions
        images = validated_data.pop('images', [])
        captions = validated_data.pop('image_captions', [])
        
        # Get booking and service info
        booking = validated_data.get('booking')
        
        # Create review object
        review = Review.objects.create(
            client=self.context['request'].user,
            provider=booking.provider,
            service=booking.service,
            **validated_data
        )
        
        # Create review images
        if images:
            for i, image_data in enumerate(images):
                caption = captions[i] if i < len(captions) else ""
                ReviewImage.objects.create(
                    review=review,
                    image=image_data,
                    caption=caption
                )
        
        return review

class ReviewProviderResponseSerializer(serializers.ModelSerializer):
    """Serializer for adding provider response to a review"""
    
    class Meta:
        model = Review
        fields = ['provider_response']
    
    def validate(self, data):
        # Check if the user is the provider of the review
        user = self.context['request'].user
        review = self.instance
        
        if review.provider != user:
            raise serializers.ValidationError(
                "You can only respond to reviews where you are the provider."
            )
            
        return data
    
    def update(self, instance, validated_data):
        # Update provider response and timestamp
        instance.provider_response = validated_data.get('provider_response')
        instance.provider_response_date = timezone.now()
        instance.save()
        
        return instance

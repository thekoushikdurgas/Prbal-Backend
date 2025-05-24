from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ServiceCategory, Service, ServiceImage, ServiceRequest, Bid, Booking, ChatMessage, Payment, Review, ReviewImage, Payout, Notification
from users.serializers import UserProfileSerializer, UserSimpleSerializer
from django.utils import timezone
from django.core.validators import MinValueValidator

User = get_user_model()

class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'

class ServiceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceImage
        fields = ['id', 'image', 'is_primary', 'created_at']

class ServiceSerializer(serializers.ModelSerializer):
    images = ServiceImageSerializer(many=True, read_only=True)
    provider = UserProfileSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(),
        write_only=True,
        source='category'
    )

    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ['provider']

    def create(self, validated_data):
        validated_data['provider'] = self.context['request'].user
        return super().create(validated_data)

class ServiceRequestListSerializer(serializers.ModelSerializer):
    """Serializer for listing service requests with minimal information"""
    customer_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name')
    bid_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'title', 'location', 'desired_datetime', 'status',
            'customer_name', 'category_name', 'bid_count', 'created_at'
        ]

    def get_customer_name(self, obj):
        return obj.customer.get_full_name()

    def get_bid_count(self, obj):
        return obj.bids.count()

class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for service requests"""
    customer = UserProfileSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(),
        write_only=True,
        source='category'
    )
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        write_only=True,
        source='service',
        required=False,
        allow_null=True
    )

    class Meta:
        model = ServiceRequest
        fields = '__all__'
        read_only_fields = ['customer', 'status']

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)

class BidListSerializer(serializers.ModelSerializer):
    """Serializer for listing bids with minimal information"""
    provider_name = serializers.SerializerMethodField()
    request_title = serializers.CharField(source='service_request.title')

    class Meta:
        model = Bid
        fields = [
            'id', 'amount', 'estimated_hours', 'proposed_datetime',
            'status', 'provider_name', 'request_title', 'created_at'
        ]

    def get_provider_name(self, obj):
        return obj.provider.get_full_name()

class BidDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for bids"""
    provider = UserProfileSerializer(read_only=True)
    service_request = ServiceRequestListSerializer(read_only=True)
    service_request_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceRequest.objects.all(),
        write_only=True,
        source='service_request'
    )

    class Meta:
        model = Bid
        fields = '__all__'
        read_only_fields = ['provider', 'status']

    def create(self, validated_data):
        validated_data['provider'] = self.context['request'].user
        return super().create(validated_data)

    def validate_service_request_id(self, value):
        if value.status != ServiceRequest.Status.OPEN:
            raise serializers.ValidationError(
                "Cannot submit bid on a request that is not open."
            )
        return value

class BidActionSerializer(serializers.Serializer):
    """Serializer for bid actions (accept/reject)"""
    action = serializers.ChoiceField(choices=['accept', 'reject'])
    message = serializers.CharField(required=False, allow_blank=True)

class AIPriceSuggestionSerializer(serializers.Serializer):
    """Serializer for AI price suggestion requests"""
    service_request_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceRequest.objects.all()
    )
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    
    class Meta:
        fields = ['service_request_id', 'provider_id']

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'stripe_charge_id', 'amount', 'status',
            'refund_id', 'error_message', 'initiated_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'initiated_at', 'updated_at', 'stripe_charge_id',
            'refund_id', 'error_message'
        ]

class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'created_at']

class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer for listing reviews with minimal information"""
    customer_name = serializers.CharField(source='customer.get_full_name')
    provider_name = serializers.CharField(source='provider.get_full_name')
    has_provider_response = serializers.BooleanField(source='provider_response.exists', read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'booking_id', 'customer_name', 'provider_name',
            'rating', 'comment', 'has_provider_response',
            'images', 'created_at'
        ]

class ReviewDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for reviews"""
    customer = UserSimpleSerializer(read_only=True)
    provider = UserSimpleSerializer(read_only=True)
    images = ReviewImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Review
        fields = [
            'id', 'booking', 'customer', 'provider',
            'rating', 'comment', 'provider_response',
            'provider_response_at', 'images', 'uploaded_images',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'customer', 'provider', 'provider_response',
            'provider_response_at', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        booking = validated_data['booking']
        
        # Set customer and provider from the booking
        validated_data['customer'] = booking.customer
        validated_data['provider'] = booking.provider
        
        review = super().create(validated_data)
        
        # Create ReviewImage instances for uploaded images
        for image_data in uploaded_images:
            ReviewImage.objects.create(review=review, image=image_data)
        
        return review

    def validate_booking(self, value):
        request = self.context['request']
        if value.customer != request.user:
            raise serializers.ValidationError(
                "You can only review bookings you've made."
            )
        if not value.can_be_reviewed:
            raise serializers.ValidationError(
                "This booking cannot be reviewed."
            )
        return value

class ProviderResponseSerializer(serializers.ModelSerializer):
    """Serializer for provider responses to reviews"""
    class Meta:
        model = Review
        fields = ['provider_response']

    def update(self, instance, validated_data):
        if instance.provider_response:
            raise serializers.ValidationError(
                "You have already responded to this review."
            )
        validated_data['provider_response_at'] = timezone.now()
        return super().update(instance, validated_data)

class BookingListSerializer(serializers.ModelSerializer):
    customer = UserSimpleSerializer(read_only=True)
    provider = UserSimpleSerializer(read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    payment_status = serializers.SerializerMethodField()
    has_review = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'customer', 'provider', 'service_name',
            'scheduled_datetime', 'agreed_price', 'status',
            'payment_status', 'has_review', 'created_at'
        ]

    def get_payment_status(self, obj):
        payment = obj.payments.order_by('-initiated_at').first()
        return payment.status if payment else None

    def get_has_review(self, obj):
        return obj.reviews.exists()

class BookingDetailSerializer(serializers.ModelSerializer):
    customer = UserSimpleSerializer(read_only=True)
    provider = UserSimpleSerializer(read_only=True)
    service_request = ServiceRequestListSerializer(read_only=True)
    accepted_bid = BidListSerializer(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    service = ServiceSerializer(read_only=True)
    review = ReviewDetailSerializer(source='reviews.first', read_only=True)
    can_be_reviewed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'customer',
            'provider', 'agreed_price', 'platform_fee',
            'cancelled_by', 'cancelled_at'
        ]

    def validate(self, data):
        if self.instance:
            # Validate status transitions
            if 'status' in data:
                current_status = self.instance.status
                new_status = data['status']
                
                # Define allowed transitions
                allowed_transitions = {
                    'scheduled': ['in_progress', 'cancelled_by_customer', 'cancelled_by_provider'],
                    'in_progress': ['completed', 'payment_pending', 'cancelled_by_provider'],
                    'payment_pending': ['completed', 'payment_failed'],
                    'completed': [],  # No transitions allowed from completed
                    'cancelled_by_customer': [],  # No transitions allowed from cancelled
                    'cancelled_by_provider': [],  # No transitions allowed from cancelled
                    'payment_failed': ['payment_pending'],
                    'disputed': ['completed', 'cancelled_by_customer', 'cancelled_by_provider']
                }

                if new_status not in allowed_transitions.get(current_status, []):
                    raise serializers.ValidationError(
                        f"Cannot transition from {current_status} to {new_status}"
                    )

            # Validate scheduled_datetime is in the future
            if 'scheduled_datetime' in data:
                if data['scheduled_datetime'] < timezone.now():
                    raise serializers.ValidationError(
                        "Scheduled datetime must be in the future"
                    )

        return data

class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['status']

    def validate_status(self, value):
        if self.instance and self.instance.provider == self.context['request'].user:
            allowed_transitions = {
                'scheduled': ['in_progress', 'cancelled_by_provider'],
                'in_progress': ['completed', 'payment_pending', 'cancelled_by_provider'],
            }
            current_status = self.instance.status
            if value not in allowed_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot transition from {current_status} to {value}"
                )
        elif not self.instance:
            pass
        else:
            raise serializers.ValidationError(
                "You are not allowed to update the status of this booking"
            )
        return value

class BookingCustomerConfirmSerializer(serializers.ModelSerializer):
    customer_completion_confirmation_flag = serializers.BooleanField(write_only=True)

    class Meta:
        model = Booking
        fields = ['customer_completion_confirmation_flag', 'customer_completion_confirmation']
        read_only_fields = ['customer_completion_confirmation']

    def update(self, instance, validated_data):
        if validated_data.get('customer_completion_confirmation_flag'):
            instance.customer_completion_confirmation = timezone.now()
            instance.status = 'completed'
            instance.save()
        return instance

class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSimpleSerializer(read_only=True)
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'booking', 'sender', 'sender_name', 'text_content',
            'media_file', 'timestamp', 'read_at'
        ]
        read_only_fields = ['id', 'sender', 'timestamp', 'read_at']
        extra_kwargs = {
            'booking': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)

class PayoutSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.get_full_name', read_only=True)
    
    class Meta:
        model = Payout
        fields = [
            'id', 'provider', 'provider_name', 'amount',
            'status', 'stripe_payout_id', 'error_message',
            'initiated_at', 'completed_at', 'updated_at'
        ]
        read_only_fields = [
            'provider', 'status', 'stripe_payout_id',
            'error_message', 'initiated_at', 'completed_at',
            'updated_at'
        ]

class PayoutInitiateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'data',
            'is_read', 'created_at', 'booking', 'bid',
            'review', 'payout'
        ]
        read_only_fields = [
            'type', 'title', 'message', 'data',
            'created_at', 'booking', 'bid',
            'review', 'payout'
        ] 
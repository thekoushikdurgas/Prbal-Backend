from rest_framework import serializers
from .models import Payment, PaymentGatewayAccount, Payout
from bookings.models import Booking
from users.serializers import PublicUserProfileSerializer
from django.utils import timezone

class PaymentGatewayAccountSerializer(serializers.ModelSerializer):
    """Serializer for payment gateway accounts"""
    
    class Meta:
        model = PaymentGatewayAccount
        fields = [
            'id', 'account_type', 'account_id', 'is_verified', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Set the user to the current user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for listing payments"""
    payer_name = serializers.CharField(source='payer.get_full_name', read_only=True)
    payee_name = serializers.CharField(source='payee.get_full_name', read_only=True)
    booking_title = serializers.CharField(source='booking.service.title', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'booking_title', 'payer', 'payer_name', 'payee',
            'payee_name', 'amount', 'payment_method', 'status', 'payment_date',
            'created_at'
        ]
        read_only_fields = fields

class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed payment view"""
    payer = PublicUserProfileSerializer(read_only=True)
    payee = PublicUserProfileSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'payer', 'payee', 'amount', 'payment_method',
            'transaction_id', 'status', 'payment_date', 'platform_fee',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for initiating a payment"""
    booking_id = serializers.UUIDField()
    payment_method = serializers.ChoiceField(choices=Payment.PAYMENT_METHOD_CHOICES)
    save_payment_method = serializers.BooleanField(required=False, default=False)
    
    def validate_booking_id(self, value):
        try:
            booking = Booking.objects.get(id=value)
            
            # Check if booking is in a valid state for payment
            valid_states = ['pending', 'confirmed']
            if booking.status not in valid_states:
                raise serializers.ValidationError(
                    f"Cannot initiate payment for a booking with status '{booking.status}'. "
                    f"Booking must be in one of these states: {', '.join(valid_states)}"
                )
            
            # Check if user is the customer of the booking
            if booking.customer != self.context['request'].user:
                raise serializers.ValidationError(
                    "You can only initiate payments for bookings where you are the customer."
                )
            
            # Check if payment already exists and is completed
            if Payment.objects.filter(booking=booking, status='completed').exists():
                raise serializers.ValidationError(
                    "This booking has already been paid for."
                )
                
            return value
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")

class PaymentConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a payment"""
    payment_id = serializers.UUIDField()
    transaction_id = serializers.CharField(required=False)
    
    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(id=value)
            
            # Check if payment is in pending state
            if payment.status != 'pending':
                raise serializers.ValidationError(
                    f"Cannot confirm a payment with status '{payment.status}'. "
                    "Payment must be in 'pending' state."
                )
            
            # Check if user is the payer
            if payment.payer != self.context['request'].user:
                raise serializers.ValidationError(
                    "You can only confirm payments that you initiated."
                )
                
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found.")

class PayoutListSerializer(serializers.ModelSerializer):
    """Serializer for listing provider payouts"""
    
    class Meta:
        model = Payout
        fields = [
            'id', 'amount', 'transaction_fee', 'net_amount', 'status',
            'created_at', 'processed_at'
        ]
        read_only_fields = fields

class PayoutDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed payout view"""
    provider = PublicUserProfileSerializer(read_only=True)
    
    class Meta:
        model = Payout
        fields = [
            'id', 'provider', 'payment_account', 'amount', 'transaction_fee',
            'net_amount', 'transaction_id', 'status', 'notes',
            'external_reference', 'created_at', 'processed_at', 'updated_at'
        ]
        read_only_fields = fields

class PayoutRequestSerializer(serializers.Serializer):
    """Serializer for requesting a payout"""
    payment_account_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    def validate_payment_account_id(self, value):
        try:
            account = PaymentGatewayAccount.objects.get(
                id=value, 
                user=self.context['request'].user
            )
            
            if not account.is_verified:
                raise serializers.ValidationError(
                    "Your payment account must be verified before requesting a payout."
                )
                
            if not account.is_active:
                raise serializers.ValidationError(
                    "This payment account is not active."
                )
                
            return value
        except PaymentGatewayAccount.DoesNotExist:
            raise serializers.ValidationError(
                "Payment account not found or does not belong to you."
            )
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Payout amount must be greater than zero."
            )
            
        # In a real implementation, you would check if the user has enough balance
        # For this implementation, we'll just validate that it's positive
        return value

class EarningsSummarySerializer(serializers.Serializer):
    """Serializer for provider earnings summary"""
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    available_for_payout = serializers.DecimalField(max_digits=10, decimal_places=2)
    completed_payouts = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_payouts = serializers.DecimalField(max_digits=10, decimal_places=2)

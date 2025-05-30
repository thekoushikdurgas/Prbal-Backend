from django.db import models
from django.conf import settings
import uuid
from bookings.models import Booking
from decimal import Decimal

# Create your models here.
class Payment(models.Model):
    """Handles all payment transactions within the app. Tracks transaction status and details."""
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('upi', 'UPI'),
        ('wallet', 'Wallet'),
        ('paypal', 'PayPal'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    )
    
    CURRENCY_CHOICES = (
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    )
    
    # Primary key and relationship fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the payment transaction")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_initiated', help_text="User initiating the payment")
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments', help_text="Related booking for this payment")
    
    # For tracking both sides of the transaction
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_made', help_text="User making the payment")
    payee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments_received', help_text="User receiving the payment")
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount of the transaction")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR', help_text="Currency of the transaction")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, help_text="Method used for payment")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', help_text="Status of the transaction")
    
    # Transaction metadata
    transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text="External transaction ID from payment processor")
    payment_date = models.DateTimeField(auto_now_add=True, help_text="Date and time of the payment")
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Fee charged by the platform")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about the payment")
    metadata = models.JSONField(default=dict, blank=True, null=True, help_text="Additional transaction metadata as JSON")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"Payment #{self.id} - {self.amount} {self.currency}"
    
    def mark_as_completed(self, transaction_id=None):
        """Mark the payment as completed"""
        if self.status != 'completed':
            self.status = 'completed'
            if transaction_id:
                self.transaction_id = transaction_id
            self.save(update_fields=['status', 'transaction_id' if transaction_id else 'status', 'updated_at'])
            return True
        return False
    
    def mark_as_failed(self, reason=None):
        """Mark the payment as failed"""
        if self.status not in ['completed', 'refunded']:
            self.status = 'failed'
            if reason:
                if not self.metadata:
                    self.metadata = {}
                self.metadata['failure_reason'] = reason
            self.save()
            return True
        return False
    
    def refund(self, reason=None, refund_transaction_id=None):
        """Process a refund for this payment"""
        if self.status == 'completed':
            self.status = 'refunded'
            
            if not self.metadata:
                self.metadata = {}
                
            refund_data = {
                'refund_date': models.functions.Now().isoformat(),
                'reason': reason,
            }
            
            if refund_transaction_id:
                refund_data['refund_transaction_id'] = refund_transaction_id
                
            self.metadata['refund'] = refund_data
            self.save()
            return True
        return False

class PaymentGatewayAccount(models.Model):
    """
    Represents a payment account with a payment gateway for a provider
    to receive funds (e.g., Stripe Connect account, PayPal account).
    """
    ACCOUNT_TYPE_CHOICES = (
        ('stripe', 'Stripe Connect'),
        ('paypal', 'PayPal'),
        ('bank', 'Direct Bank Transfer'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_accounts')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    account_id = models.CharField(max_length=255, help_text="External account ID in the payment gateway")
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    account_details = models.JSONField(default=dict, blank=True, help_text="Additional account details as JSON")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment Gateway Account'
        verbose_name_plural = 'Payment Gateway Accounts'
        unique_together = ['user', 'account_type']
    
    def __str__(self):
        return f"{self.user.username}'s {self.get_account_type_display()} account"

class Payout(models.Model):
    """
    Represents a payout to a provider for completed services.
    """
    PAYOUT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payouts')
    payment_account = models.ForeignKey(PaymentGatewayAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYOUT_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    external_reference = models.CharField(max_length=255, blank=True, null=True, help_text="Reference ID in external payment system")
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payout'
        verbose_name_plural = 'Payouts'
    
    def __str__(self):
        return f"Payout #{self.id} - {self.amount} to {self.provider.username}"
    
    def save(self, *args, **kwargs):
        # Calculate net amount if not explicitly set
        if not self.net_amount:
            self.net_amount = self.amount - self.transaction_fee
        super().save(*args, **kwargs)

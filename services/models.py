from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

BOOKING_STATUS_CHOICES = [
    ('scheduled', 'Scheduled'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('payment_pending', 'Payment Pending'),
    ('paid', 'Paid'),
    ('cancelled_by_customer', 'Cancelled by Customer'),
    ('cancelled_by_provider', 'Cancelled by Provider'),
    ('payment_failed', 'Payment Failed'),
    ('disputed', 'Disputed'),
]

PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('held_in_escrow', 'Held in Escrow'),
    ('released_to_provider', 'Released to Provider'),
    ('refunded', 'Refunded'),
    ('failed', 'Failed'),
]

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Service Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class ServiceImage(models.Model):
    service = models.ForeignKey(
        'Service',
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='service_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"Image for {self.service.name}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary image per service
            ServiceImage.objects.filter(service=self.service, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

class Service(models.Model):
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='services'
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name='services'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    min_hours = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    max_hours = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True
    )
    service_area = models.CharField(max_length=255)
    required_tools = models.TextField(blank=True)
    availability = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['service_area']),
            models.Index(fields=['hourly_rate']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} by {self.provider.get_full_name()}"

    def clean(self):
        if self.max_hours and self.max_hours < self.min_hours:
            raise models.ValidationError({
                'max_hours': 'Maximum hours must be greater than or equal to minimum hours.'
            })
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class ServiceRequest(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open for Bids'
        PENDING_BIDS = 'PENDING_BIDS', 'Pending Bids'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_requests'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_requests'
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name='service_requests'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    desired_datetime = models.DateTimeField()
    estimated_hours = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    requirements = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['location']),
            models.Index(fields=['desired_datetime']),
        ]

    def __str__(self):
        return f"{self.title} by {self.customer.get_full_name()}"

    def clean(self):
        if self.desired_datetime and self.desired_datetime < timezone.now():
            raise models.ValidationError({
                'desired_datetime': 'Desired datetime must be in the future.'
            })
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Bid(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        COUNTERED = 'COUNTERED', 'Countered'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='bids'
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_bids'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    estimated_hours = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    proposed_datetime = models.DateTimeField()
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['amount']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['service_request', 'provider'],
                condition=models.Q(status='SUBMITTED'),
                name='unique_active_bid_per_provider'
            )
        ]

    def __str__(self):
        return f"Bid on {self.service_request.title} by {self.provider.get_full_name()}"

    def clean(self):
        if self.proposed_datetime and self.proposed_datetime < timezone.now():
            raise models.ValidationError({
                'proposed_datetime': 'Proposed datetime must be in the future.'
            })
        if self.service_request.status != ServiceRequest.Status.OPEN:
            raise models.ValidationError(
                'Cannot submit bid on a request that is not open.'
            )
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Booking(models.Model):
    service_request = models.ForeignKey(
        'ServiceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    accepted_bid = models.OneToOneField(
        'Bid',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booking'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_bookings'
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_bookings'
    )
    service = models.ForeignKey(
        'Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    scheduled_datetime = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duration in minutes"
    )
    location_address = models.TextField(blank=True)
    agreed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text="Platform fee calculated at booking creation"
    )
    status = models.CharField(
        max_length=30,
        choices=BOOKING_STATUS_CHOICES,
        default='scheduled'
    )
    customer_completion_confirmation = models.DateTimeField(
        null=True,
        blank=True
    )
    provider_completion_confirmation = models.DateTimeField(
        null=True,
        blank=True
    )
    completion_grace_period = models.DurationField(
        default=timezone.timedelta(days=3),
        help_text="Grace period for customer to confirm completion"
    )
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_bookings'
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_datetime']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_datetime']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Booking {self.id} - {self.service.name if self.service else 'No Service'}"

    def clean(self):
        if self.scheduled_datetime and self.scheduled_datetime < timezone.now():
            raise models.ValidationError({
                'scheduled_datetime': 'Scheduled datetime must be in the future.'
            })
        super().clean()

    def save(self, *args, **kwargs):
        if not self.platform_fee and self.agreed_price:
            # Calculate platform fee (e.g., 10% of agreed price)
            self.platform_fee = self.agreed_price * 0.10
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_completed(self):
        return bool(
            self.status == 'completed' and
            self.customer_completion_confirmation and
            self.provider_completion_confirmation
        )

    @property
    def can_be_reviewed(self):
        return self.status in ['completed', 'paid'] and not self.reviews.exists()

class Review(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_reviews'
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_reviews'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    provider_response = models.TextField(blank=True)
    provider_response_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['booking'],
                name='unique_review_per_booking'
            )
        ]

    def __str__(self):
        return f"Review for {self.provider.get_full_name()} by {self.customer.get_full_name()}"

    def clean(self):
        if self.booking.customer != self.customer:
            raise models.ValidationError({
                'customer': 'Review can only be created by the booking customer.'
            })
        if self.booking.provider != self.provider:
            raise models.ValidationError({
                'provider': 'Review must be for the booking provider.'
            })
        if not self.booking.can_be_reviewed:
            raise models.ValidationError(
                'Booking must be completed or paid and not already reviewed.'
            )
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class ReviewImage(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='review_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Image for review {self.review.id}"

class Payment(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    stripe_charge_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe Charge/PaymentIntent ID"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    refund_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Stripe Refund ID if refunded"
    )
    error_message = models.TextField(blank=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['stripe_charge_id']),
        ]

    def __str__(self):
        return f"Payment {self.id} for Booking {self.booking.id}"

class ChatMessage(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_chat_messages'
    )
    text_content = models.TextField(blank=True)
    media_file = models.FileField(
        upload_to='chat_media/',
        blank=True,
        null=True,
        help_text="Image or file attachment"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the recipient read the message"
    )

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['booking', 'timestamp']),
        ]

    def __str__(self):
        return f"Message from {self.sender.get_full_name()} in Booking {self.booking.id}"

class Payout(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    stripe_payout_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Stripe Payout ID'
    )
    error_message = models.TextField(blank=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['initiated_at']),
            models.Index(fields=['provider', 'status']),
        ]

    def __str__(self):
        return f"Payout {self.id} - {self.provider.get_full_name()} - {self.amount}"

class Notification(models.Model):
    class Type(models.TextChoices):
        NEW_BID = 'NEW_BID', 'New Bid'
        BID_ACCEPTED = 'BID_ACCEPTED', 'Bid Accepted'
        BOOKING_CONFIRMED = 'BOOKING_CONFIRMED', 'Booking Confirmed'
        SERVICE_COMPLETED = 'SERVICE_COMPLETED', 'Service Completed'
        PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', 'Payment Received'
        PAYOUT_UPDATE = 'PAYOUT_UPDATE', 'Payout Update'
        NEW_REVIEW = 'NEW_REVIEW', 'New Review'
        REVIEW_RESPONSE = 'REVIEW_RESPONSE', 'Review Response'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(
        max_length=50,
        choices=Type.choices
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(
        default=dict,
        help_text='Additional data related to the notification'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional relations to related objects
    booking = models.ForeignKey(
        'Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    bid = models.ForeignKey(
        'Bid',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    review = models.ForeignKey(
        'Review',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    payout = models.ForeignKey(
        'Payout',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f"{self.type} for {self.user.get_full_name()}"

    @classmethod
    def create_notification(cls, user, type, title, message, **kwargs):
        """
        Helper method to create notifications with related objects
        """
        notification_data = {
            'user': user,
            'type': type,
            'title': title,
            'message': message,
        }
        
        # Add optional related objects if provided
        for field in ['booking', 'bid', 'review', 'payout']:
            if field in kwargs:
                notification_data[field] = kwargs.pop(field)
        
        # Any remaining kwargs go into the data JSON field
        if kwargs:
            notification_data['data'] = kwargs
        
        return cls.objects.create(**notification_data)

class Chat(models.Model):
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='chats'
    )
    booking = models.OneToOneField(
        'Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat'
    )
    service_request = models.OneToOneField(
        'ServiceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        return f"Chat {self.id} - {', '.join(user.get_full_name() for user in self.participants.all())}"

    def can_participate(self, user):
        """Check if a user can participate in this chat"""
        if self.booking:
            return user in [self.booking.customer, self.booking.provider]
        elif self.service_request:
            if user == self.service_request.customer:
                return True
            return Bid.objects.filter(
                service_request=self.service_request,
                provider=user,
                status='SUBMITTED'
            ).exists()
        return self.participants.filter(id=user.id).exists()

class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    media_file = models.FileField(
        upload_to='chat_media/',
        null=True,
        blank=True,
        help_text="Image or file attachment"
    )
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='read_messages',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['chat', 'created_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender.get_full_name()} in Chat {self.chat.id}"

    def mark_read_by(self, user):
        """Mark message as read by a user"""
        if user != self.sender and user in self.chat.participants.all():
            self.read_by.add(user)

from django.contrib import admin
from .models import (
    ServiceCategory, Service, ServiceImage,
    ServiceRequest, Bid, Booking, ChatMessage,
    Payment, Review, ReviewImage, Payout,
    Notification, Chat, Message
)

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'booking', 'service_request', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['booking__id', 'service_request__id']
    raw_id_fields = ['participants', 'booking', 'service_request']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'sender', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'sender__email']
    raw_id_fields = ['chat', 'sender', 'read_by']

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'provider', 'amount', 'status',
        'initiated_at', 'completed_at'
    ]
    list_filter = ['status']
    search_fields = ['provider__email', 'stripe_payout_id']
    readonly_fields = [
        'stripe_payout_id', 'error_message',
        'initiated_at', 'updated_at', 'completed_at'
    ]

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'type', 'title',
        'is_read', 'created_at'
    ]
    list_filter = ['type', 'is_read']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at']

# Register other models
admin.site.register(ServiceCategory)
admin.site.register(Service)
admin.site.register(ServiceImage)
admin.site.register(ServiceRequest)
admin.site.register(Bid)
admin.site.register(Booking)
admin.site.register(ChatMessage)
admin.site.register(Payment)
admin.site.register(Review)
admin.site.register(ReviewImage)

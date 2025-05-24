from django.urls import re_path
from . import chat_consumer, notification_consumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<chat_id>\d+)/$', chat_consumer.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/(?P<user_id>\d+)/$', notification_consumer.NotificationConsumer.as_asgi()),
] 
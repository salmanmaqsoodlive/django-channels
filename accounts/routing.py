from django.urls import re_path, path
from .consumers import MySyncConsumer

websocket_urlpatterns = [
    re_path(r"ws/sc/$", MySyncConsumer.as_asgi()),
    # Add other WebSocket URL patterns as needed
]

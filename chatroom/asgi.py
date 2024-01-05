# asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatroom.settings")
import django
django.setup()
import accounts.routing  # Import your routing configuration




application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                accounts.routing.websocket_urlpatterns  # Use your WebSocket URL patterns
            )
        ),
    }
)



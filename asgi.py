import os
import sys
from pathlib import Path

# Add the project root to sys.path to make 'mkani' module importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import mkani.apps.notifications.routing as notifications_routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mkani.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            notifications_routing.websocket_urlpatterns
        )
    ),
})

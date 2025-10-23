import os
import sys
from pathlib import Path

# Add the project root to sys.path to make 'mkani' module importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.prod')
application = get_wsgi_application()

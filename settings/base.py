import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'replace-me-in-prod')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
#ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
ALLOWED_HOSTS = ['*' , '.railway.app']

INSTALLED_APPS = [
    'django_filters',
    'drf_spectacular',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',

        # local apps
        'apps.accounts',
        'apps.buildings',
        'apps.packages',
        'apps.payments',
        'apps.notifications',
        'apps.core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.accounts.middleware.AutoRefreshTokenMiddleware',
    'middlewares.JWTAuthFromCookieMiddleware',
]

ROOT_URLCONF = 'urls'
WSGI_APPLICATION = 'wsgi.application'
ASGI_APPLICATION = 'asgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL')
    )
}

AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.EmailBackend',  # تسجيل الدخول بالإيميل
    'django.contrib.auth.backends.ModelBackend',  # الاحتياطي
]

LANGUAGE_CODE = 'ar'
LANGUAGES = [('ar', 'Arabic'), ('en', 'English')]
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.accounts.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_COOKIE': 'access_token',
    'AUTH_COOKIE_SECURE': True,
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_SAMESITE': 'None',
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Channels (basic)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Celery
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'MaKaNiii2025@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'nukx tukx cqay griy')  # App password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# External services placeholders
PAYMOB_API_KEY = os.environ.get('PAYMOB_API_KEY', '')
PAYMOB_INTEGRATION_ID = os.environ.get('PAYMOB_INTEGRATION_ID', '')
PAYMOB_IFRAME_ID = os.environ.get('PAYMOB_IFRAME_ID', '')
PAYMOB_MODE = os.environ.get('PAYMOB_MODE', 'mock')
SAHEL_API_KEY = os.environ.get('SAHEL_API_KEY', '')
SAHEL_MODE = os.environ.get('SAHEL_MODE', 'mock')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Google OAuth settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv("GOOGLE_CLIENT_ID")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# drf-spectacular OpenAPI settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Mkani API',
    'DESCRIPTION': 'OpenAPI schema for Mkani platform',
    'VERSION': '1.0.0',
    # Add security definitions, etc. here if needed
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'https://mkani-frontend.vercel.app',
    'https://mkani-frontend-r8iipcgi8-salma-mohameds-projects-3db72cdf.vercel.app',
    'https://terrific-success-production.up.railway.app',
    'https://mkani-production.up.railway.app',
]

# Allow specific origins only (required for cookies to work with cross-site requests)
CORS_ALLOW_ALL_ORIGINS = False

# Allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

# Allow all headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Cookie settings
SESSION_COOKIE_SECURE = True  # True in production with HTTPS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SAMESITE = 'None'
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://mkani-frontend-r8iipcgi8-salma-mohameds-projects-3db72cdf.vercel.app",
    "https://terrific-success-production.up.railway.app",
    "https://mkani-production.up.railway.app",
]

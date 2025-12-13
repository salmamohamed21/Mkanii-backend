from .base import *

# Dev overrides
DEBUG = True

# Database for local PostgreSQL
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mkani_db',    # Replace with your database name
        'USER': 'postgres',    # Replace with your database user
        'PASSWORD': 'mosa$555#Mo', # Replace with your database password
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# In base.py, some cookie settings are set based on `not DEBUG`.
# Since DEBUG is True here, those will correctly evaluate to False for local dev,
# which is required for testing on http://localhost.
# For example:
# AUTH_COOKIE_SECURE becomes False
# SESSION_COOKIE_SECURE becomes False
# CSRF_COOKIE_SECURE becomes False
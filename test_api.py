import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

# Create a test client
client = Client()

# Login
login_response = client.post('/api/auth/login/', {
    'email': 'salmam28@gmail.com',
    'password': 'Salma@123'
}, content_type='application/json')

print('Login response status:', login_response.status_code)
print('Login response content:', login_response.content.decode())

# Test the endpoint
endpoint_response = client.get('/buildings/my-buildings/')
print('Endpoint response status:', endpoint_response.status_code)
print('Endpoint response content:', endpoint_response.content.decode())

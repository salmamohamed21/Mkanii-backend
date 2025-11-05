import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.accounts.views.auth import RegisterView
from apps.accounts.models import ResidentProfile
from apps.buildings.models import Unit

User = get_user_model()

def test_register_owner_without_area_rooms():
    # Create a mock request with owner data WITHOUT area and rooms_count
    factory = RequestFactory()
    data = {
        'email': 'testowner2@example.com',
        'username': 'testowner2',
        'full_name': 'Test Owner 2',
        'phone_number': '1234567891',
        'national_id': '1234567890124',
        'password': 'TestPass123!',
        'roles': ['resident'],
        'resident_type': 'owner',
        'building_name': 'Test Building 2',
        'address': 'Test Address 2',
        'floor_number': 2,
        'apartment_number': '202',
        # No 'area' and 'rooms_count' provided
    }

    # Create a POST request
    request = factory.post('/register/', data=data)
    # Manually set request.data since RequestFactory doesn't set it
    request.data = data

    # Initialize the view properly
    view = RegisterView()
    view.format_kwarg = None  # Set required attributes
    view.request = request

    try:
        response = view.create(request)
        print("Registration Response Status:", response.status_code)
        print("Response Data:", response.data)

        # Check if user was created
        user = User.objects.get(email='testowner2@example.com')
        print("User Created:", user.full_name)

        # Check ResidentProfile
        rp = ResidentProfile.objects.get(user=user)
        print("ResidentProfile Created:")
        print("  Resident Type:", rp.resident_type)
        print("  Area:", rp.area)
        print("  Rooms Count:", rp.rooms_count)

        # Check Unit
        unit = rp.unit
        if unit:
            print("Unit Created:")
            print("  Area:", unit.area)
            print("  Rooms Count:", unit.rooms_count)
        else:
            print("No Unit Created")

    except Exception as e:
        print("Error during registration:", str(e))

if __name__ == '__main__':
    test_register_owner_without_area_rooms()

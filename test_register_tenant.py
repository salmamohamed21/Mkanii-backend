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
from apps.buildings.models import Building, Unit

User = get_user_model()

def test_register_tenant():
    # Clean up any existing data first
    User.objects.filter(email__in=['owner@example.com', 'testtenant@example.com']).delete()
    ResidentProfile.objects.filter(user__email__in=['owner@example.com', 'testtenant@example.com']).delete()
    Building.objects.filter(name='Owner Building').delete()

    # First, create a mock owner user
    owner = User.objects.create_user(
        email='owner@example.com',
        username='owner',
        full_name='Owner User',
        phone_number='0987654321',
        national_id='9876543210987',
        password='OwnerPass123!'
    )

    # Clean up any existing tenant data
    User.objects.filter(phone_number='1234567890').delete()
    User.objects.filter(national_id='1234567890123').delete()

    # Create a building and unit for the owner
    building = Building.objects.create(
        union_head=owner,
        name='Owner Building',
        address='Owner Address',
        total_units=10,
        total_floors=5,
        units_per_floor=2,
        subscription_plan='basic'
    )
    unit = Unit.objects.create(
        building=building,
        floor_number=1,
        apartment_number='101',
        area=100.0,
        rooms_count=3,
        status='available'
    )

    # Create owner ResidentProfile
    ResidentProfile.objects.create(
        user=owner,
        unit=unit,
        resident_type='owner',
        area=100.0,
        rooms_count=3,
        status='active',
        is_present=True
    )

    # Now, create a mock request with tenant data
    factory = RequestFactory()
    data = {
        'email': 'testtenant@example.com',
        'username': 'testtenant',
        'full_name': 'Test Tenant',
        'phone_number': '1234567890',
        'national_id': '1234567890123',
        'password': 'TenantPass123!',
        'roles': ['resident'],
        'resident_type': 'tenant',
        'building_id': building.id,
        'floor_number': 1,
        'apartment_number': '101',
        'owner_national_id': owner.national_id,
        'rental_start_date': '2023-01-01',
        'rental_end_date': '2024-01-01',
        'rental_value': 500.00,
    }

    # Create a POST request
    request = factory.post('/register/', data=data)
    request.data = data

    # Initialize the view
    view = RegisterView()
    view.format_kwarg = None
    view.request = request

    try:
        response = view.create(request)
        print("Registration Response Status:", response.status_code)
        print("Response Data:", response.data)

        if response.status_code == 201:
            # Check if user was created
            user = User.objects.get(email='testtenant@example.com')
            print("User Created:", user.full_name)

            # Check ResidentProfile
            rp = ResidentProfile.objects.get(user=user)
            print("ResidentProfile Created:")
            print("  Resident Type:", rp.resident_type)
            print("  Owner:", rp.owner.full_name if rp.owner else None)
            print("  Rental Start Date:", rp.rental_start_date)
            print("  Rental End Date:", rp.rental_end_date)
            print("  Rental Value:", rp.rental_value)
            print("  Status:", rp.status)
        else:
            print("Registration Failed")

    except Exception as e:
        print("Error during registration:", str(e))

if __name__ == '__main__':
    test_register_tenant()

import os
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
django.setup()

from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from apps.accounts.views.auth import ResidentProfileViewSet
from apps.buildings.models import Building, Unit

User = get_user_model()

class AddResidentApartmentTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(email='testuser@example.com', password='Testpassword123!', full_name='Test User', national_id='12345678901234')
        self.building = Building.objects.create(name='Test Building', address='123 Test St', total_floors=5, total_units=10)
        self.unit = Unit.objects.create(building=self.building, floor_number=1, apartment_number='101')

    def test_add_resident_apartment(self):
        data = {
            'user': self.user.id,
            'unit': self.unit.id,
            'resident_type': 'owner',
        }

        request = self.factory.post('/api/accounts/residents/', data=data)
        request.user = self.user

        view = ResidentProfileViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)
        print("Test passed: Resident apartment added successfully.")

if __name__ == '__main__':
    # To run this test, use the Django test runner:
    # python manage.py test mkani.test_add_resident_apartment
    pass

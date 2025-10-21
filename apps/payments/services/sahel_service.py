import requests
from django.conf import settings

class SahelService:
    BASE_URL = getattr(settings, 'SAHEL_BASE_URL', 'https://api.sahel.com')
    API_KEY = getattr(settings, 'SAHEL_API_KEY', '')
    SECRET_KEY = getattr(settings, 'SAHEL_SECRET_KEY', '')

    @classmethod
    def authenticate(cls):
        url = f"{cls.BASE_URL}/auth"
        payload = {"api_key": cls.API_KEY, "secret_key": cls.SECRET_KEY}
        response = requests.post(url, json=payload)
        return response.json().get('token')

    @classmethod
    def inquire_bill(cls, account_number, service_type):
        url = f"{cls.BASE_URL}/bills/inquiry"
        headers = {"Authorization": f"Bearer {cls.authenticate()}"}
        payload = {
            "api_key": cls.API_KEY,
            "account_number": account_number,
            "service_type": service_type
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return {
            "bill_number": data.get("bill_number"),
            "amount_due": data.get("amount_due", 0),
            "due_date": data.get("due_date")
        }

    @classmethod
    def pay_bill(cls, bill_number, amount):
        url = f"{cls.BASE_URL}/bills/pay"
        headers = {"Authorization": f"Bearer {cls.authenticate()}"}
        payload = {"bill_number": bill_number, "amount": amount}
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

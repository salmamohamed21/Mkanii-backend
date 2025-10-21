import requests
from django.conf import settings

class PaymobService:
    BASE_URL = 'https://accept.paymob.com/api'
    API_KEY = getattr(settings, 'PAYMOB_API_KEY', '')
    INTEGRATION_ID = getattr(settings, 'PAYMOB_INTEGRATION_ID', '')

    @classmethod
    def authenticate(cls):
        url = f"{cls.BASE_URL}/auth/tokens"
        payload = {"api_key": cls.API_KEY}
        response = requests.post(url, json=payload)
        return response.json().get('token')

    @classmethod
    def create_order(cls, auth_token, amount, currency='EGP'):
        url = f"{cls.BASE_URL}/ecommerce/orders"
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {
            "amount_cents": int(amount * 100),
            "currency": currency,
            "items": []
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    @classmethod
    def create_payment_key(cls, auth_token, order_id, amount, billing_data):
        url = f"{cls.BASE_URL}/acceptance/payment_keys"
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {
            "amount_cents": int(amount * 100),
            "currency": "EGP",
            "order_id": order_id,
            "billing_data": billing_data,
            "integration_id": cls.INTEGRATION_ID
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    @classmethod
    def process_payment(cls, amount, billing_data):
        auth_token = cls.authenticate()
        order = cls.create_order(auth_token, amount)
        order_id = order.get('id')
        payment_key = cls.create_payment_key(auth_token, order_id, amount, billing_data)
        return payment_key.get('token')

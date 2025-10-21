from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests

User = get_user_model()

class GoogleLoginView(APIView):
    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response({"error": "Missing id_token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # تحقق من صحة التوكن مع Google
            idinfo = id_token.verify_oauth2_token(token, requests.Request())

            email = idinfo.get("email")
            name = idinfo.get("name")

            user, _ = User.objects.get_or_create(email=email, defaults={"full_name": name})

            refresh = RefreshToken.for_user(user)
            response = Response({"success": True})
            response.set_cookie("access_token", str(refresh.access_token), httponly=True)
            response.set_cookie("refresh_token", str(refresh), httponly=True)
            return response

        except ValueError:
            return Response({"error": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

class AutoRefreshTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        access_token = request.COOKIES.get("access_token")
        refresh_token = request.COOKIES.get("refresh_token")

        if not access_token or not refresh_token:
            return None  # مفيش توكنات، تجاهل

        try:
            token = AccessToken(access_token)
            # لو التوكن صالح، كمل الطلب عادي
            return None
        except TokenError:
            # التوكن انتهى → نجرب نجدد باستخدام الـ refresh_token
            try:
                refresh = RefreshToken(refresh_token)
                new_access_token = str(refresh.access_token)

                # ضيف الهيدر الجديد علشان باقي الكود يشتغل بيه
                request.META["HTTP_AUTHORIZATION"] = f"Bearer {new_access_token}"
                request.new_access_token = new_access_token
                return None
            except TokenError:
                # لو حتى الـ refresh_token انتهى → لازم المستخدم يسجل دخول تاني
                return JsonResponse({"detail": "Session expired, please login again."}, status=401)

    def process_response(self, request, response):
        # لو حصل تجديد للتوكن نحفظه في الكوكي
        if hasattr(request, "new_access_token"):
            response.set_cookie(
                "access_token",
                request.new_access_token,
                httponly=True,
                secure=False,
                samesite="Lax",
            )
        return response

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads access_token from cookies
    instead of Authorization header.
    """

    def authenticate(self, request):
        """
        Override authenticate to read token from cookies.
        """
        # Get token from cookie
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            return None

        # Validate the token
        validated_token = self.get_validated_token(access_token)

        try:
            user = self.get_user(validated_token)
        except Exception as e:
            logger.warning(f"Failed to get user from token: {e}")
            return None

        return (user, validated_token)

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return 'Bearer realm="api"'

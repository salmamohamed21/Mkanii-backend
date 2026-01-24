import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class JWTAuthFromCookieMiddleware(MiddlewareMixin):
    def process_request(self, request):
        access_token = request.COOKIES.get('access_token')
        if access_token and 'HTTP_AUTHORIZATION' not in request.META:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'

class CORSDebugMiddleware(MiddlewareMixin):
    """Debug middleware to log CORS-related information"""
    def process_request(self, request):
        origin = request.META.get('HTTP_ORIGIN', 'No origin header')
        logger.debug(f"Request Origin: {origin}")
        logger.debug(f"Request Method: {request.method}")
        logger.debug(f"Request Path: {request.path}")
        return None
    
    def process_response(self, request, response):
        cors_header = response.get('Access-Control-Allow-Origin', 'Not set')
        if request.META.get('HTTP_ORIGIN'):
            logger.debug(f"Response CORS Header: {cors_header}")
        return response

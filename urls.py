from django.contrib import admin
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views.social_login import GoogleLoginView
from django.http import HttpResponse

def home(request):
    return HttpResponse("Hello, Railway is working!")

urlpatterns = [
    path('', home),  # 👈 ده المسار الرئيسي
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/social/google/', GoogleLoginView.as_view(), name='google_login'),
    path('api/auth/', include('apps.accounts.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('payments/', include('apps.payments.urls')),
    path('packages/', include('apps.packages.urls')),
    path('buildings/', include('apps.buildings.urls')),
    path('admin/', admin.site.urls),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/buildings/', include('apps.buildings.urls')),
    path('api/packages/', include('apps.packages.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/core/', include('apps.core.urls')),
    path('api/public/', include('apps.buildings.urls')),
    path('rentals/', include('apps.rentals.urls')),
]

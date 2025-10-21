from django.contrib import admin
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from mkani.apps.accounts.views.social_login import GoogleLoginView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/social/google/', GoogleLoginView.as_view(), name='google_login'),
    path('api/auth/', include('mkani.apps.accounts.urls')),
    path('notifications/', include('mkani.apps.notifications.urls')),
    path('payments/', include('mkani.apps.payments.urls')),
    path('packages/', include('mkani.apps.packages.urls')),
    path('maintenance/', include('mkani.apps.maintenance.urls')),
    path('buildings/', include('mkani.apps.buildings.urls')),
    path('admin/', admin.site.urls),
    path('api/accounts/', include('mkani.apps.accounts.urls')),
    path('api/buildings/', include('mkani.apps.buildings.urls')),
    path('api/packages/', include('mkani.apps.packages.urls')),
    path('api/payments/', include('mkani.apps.payments.urls')),
    path('api/maintenance/', include('mkani.apps.maintenance.urls')),
    path('api/notifications/', include('mkani.apps.notifications.urls')),
    path('api/core/', include('mkani.apps.core.urls')),
    path('api/public/', include('mkani.apps.buildings.urls')),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BuildingViewSet, PublicBuildingNamesView, PublicBuildingsListView

router = DefaultRouter()
router.register(r'', BuildingViewSet, basename='building')

urlpatterns = [
    path('building-names/', PublicBuildingNamesView.as_view(), name='public-building-names'),
    path('', include(router.urls)),
    
    path('public-buildings-list/', PublicBuildingsListView.as_view(), name='public-buildings-list'),
]

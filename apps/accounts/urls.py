from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.auth import (
    RegisterView, LoginView, LogoutView,
    PasswordResetView, PasswordResetConfirmView, PasswordChangeView, ProfileView,
    UpdateProfileView, UserRolesView, AddRoleView,
    BuildingViewSet, ResidentProfileViewSet, TechnicianProfileViewSet,
    search_by_national_id, get_resident_profile_data, get_technician_profile_data, get_union_head_profile_data, #WelcomeView
)
from .views.social_login import GoogleLoginView

router = DefaultRouter()
router.register("union-heads", BuildingViewSet)
router.register("residents", ResidentProfileViewSet)
router.register("technicians", TechnicianProfileViewSet)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-reset/", PasswordResetView.as_view(), name="password-reset"),
    path("password-reset-confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("password-change/", PasswordChangeView.as_view(), name="password-change"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/update/", UpdateProfileView.as_view(), name="profile-update"),
    path("profile/roles/", UserRolesView.as_view(), name="profile-roles"),
    path("profile/add-role/", AddRoleView.as_view(), name="add-role"),
    path("profile/resident-data/", get_resident_profile_data, name="resident_profile_data"),
    path("profile/technician-data/", get_technician_profile_data, name="technician_profile_data"),
    path("profile/union-head-data/", get_union_head_profile_data, name="union_head_profile_data"),
    path("search-by-national-id/<str:national_id>/", search_by_national_id, name="search_by_national_id"),
    path("google-login/", GoogleLoginView.as_view(), name="google_login"),
    #path("welcome/", WelcomeView.as_view(), name="welcome"),
    path("", include(router.urls)),
]

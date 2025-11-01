from django.contrib import admin
from .models import User, ResidentProfile



@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "is_active", "is_staff")
    search_fields = ("email", "full_name")
    list_filter = ("is_staff", "is_active")







@admin.register(ResidentProfile)
class ResidentProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "unit", "resident_type", "status", "created_at")
    search_fields = ("user__full_name", "unit__building__name")
    list_filter = ("status", "resident_type")

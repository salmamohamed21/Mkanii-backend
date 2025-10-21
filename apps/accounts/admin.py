from django.contrib import admin
from .models import User, ResidentProfile, TechnicianProfile, TechnicianSchedule



@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "is_active", "is_staff")
    search_fields = ("email", "full_name")
    list_filter = ("is_staff", "is_active")





@admin.register(ResidentProfile)
class ResidentProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "building", "floor_number", "apartment_number", "created_at")
    search_fields = ("user__full_name", "building__name")
    list_filter = ("status",)


@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "specialization", "work_area", "employment_status", "created_at")
    search_fields = ("user__full_name", "specialization")


@admin.register(TechnicianSchedule)
class TechnicianScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "technician", "day_of_week", "start_time", "end_time", "shift_type")

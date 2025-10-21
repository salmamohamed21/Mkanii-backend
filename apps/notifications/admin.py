from django.contrib import admin
from .models import Notification

# Register models for admin
admin.site.register([Notification])

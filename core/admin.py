from django.contrib import admin
from .models import AppVersion


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ("platform", "latest_version", "min_version", "updated_at")

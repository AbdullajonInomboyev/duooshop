from django.contrib import admin
from .models import Banner, PromoScreen


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "link_type", "order", "is_active", "starts_at", "ends_at")
    list_editable = ("order", "is_active")


@admin.register(PromoScreen)
class PromoScreenAdmin(admin.ModelAdmin):
    list_display = ("title", "placement", "skip_after_seconds", "is_active")
    list_filter = ("placement", "is_active")

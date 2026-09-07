from django.contrib import admin
from .models import AppVersion


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ("platform", "latest_version", "min_version", "updated_at")


from .models import SiteConfig


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    list_display = ("admin_phone", "admin_name", "updated_at")

    def has_add_permission(self, request):
        # Faqat bitta yozuv (singleton) — mavjud bo'lsa qo'shib bo'lmaydi
        return not SiteConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
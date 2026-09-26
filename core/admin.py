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

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("shop_name", "phone", "short_message", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("shop_name", "phone", "message")
    readonly_fields = ("shop", "shop_name", "phone", "message", "created_at")
    list_editable = ("is_read",)
    date_hierarchy = "created_at"

    @admin.display(description="Fikr")
    def short_message(self, obj):
        return obj.message[:60] + ("..." if len(obj.message) > 60 else "")

    def has_add_permission(self, request):
        return False  # faqat ilovadan keladi
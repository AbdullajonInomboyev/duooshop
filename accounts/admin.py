from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Region, District, Shop
from .admin_filters import RegionFilter, ChainedDistrictFilter


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "is_active")
    list_filter = ("region",)
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("phone", "full_name", "role", "region", "is_active")
    list_filter = ("role", "region", "is_active")
    search_fields = ("phone", "full_name", "username")
    ordering = ("phone",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Shaxsiy", {"fields": ("full_name", "phone", "email", "role", "region", "push_token")}),
        ("Huquqlar", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",),
                "fields": ("username", "phone", "role", "password1", "password2")}),
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "region", "district", "approved_badge",
                    "debt_balance", "is_new", "is_active", "created_at")
    list_filter = (RegionFilter, ChainedDistrictFilter,
                   "is_approved", "is_new", "is_active")
    search_fields = ("name", "owner__phone", "owner__full_name")
    readonly_fields = ("created_at",)
    list_editable = ("is_new",)
    actions = ["approve_shops", "unapprove_shops"]

    @admin.display(description="Tasdiq")
    def approved_badge(self, obj):
        from django.utils.html import format_html
        if obj.is_approved:
            return format_html(
                '<span style="color:#009D4D;font-weight:600">✓ Tasdiqlangan</span>')
        return format_html(
            '<span style="color:#f9a825;font-weight:600">⏳ Kutilmoqda</span>')

    @admin.action(description="✅ Tasdiqlash (buyurtma bera oladi)")
    def approve_shops(self, request, queryset):
        n = queryset.update(is_approved=True)
        self.message_user(request, f"{n} ta do'kon tasdiqlandi.")

    @admin.action(description="⏸ Tasdiqni bekor qilish (deaktiv)")
    def unapprove_shops(self, request, queryset):
        n = queryset.update(is_approved=False)
        self.message_user(request, f"{n} ta do'kon deaktiv qilindi.")
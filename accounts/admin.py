from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Region, District, Shop


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
    list_display = ("name", "owner", "region", "district",
                    "debt_balance", "is_new", "is_active", "created_at")
    list_filter = ("region", "district", "is_new", "is_active")
    search_fields = ("name", "owner__phone", "owner__full_name")
    readonly_fields = ("created_at",)
    list_editable = ("is_new",)

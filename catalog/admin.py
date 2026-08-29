from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Brand, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_official", "order", "is_active")
    list_filter = ("category", "is_official", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "price", "unit",
                    "stock", "is_new", "is_promo", "is_active")
    list_filter = ("category", "brand", "is_new", "is_promo", "is_active")
    list_editable = ("price", "stock", "is_active")
    search_fields = ("name", "brand__name")
    readonly_fields = ("created_at", "updated_at")

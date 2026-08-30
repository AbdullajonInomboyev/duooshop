from django.contrib import admin
from django import forms
from .models import Category, Brand, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "categories_list", "is_official", "order", "is_active")
    list_filter = ("categories", "is_official", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("categories",)  # kategoriyalarni qulay tanlash

    @admin.display(description="Kategoriyalar")
    def categories_list(self, obj):
        return ", ".join(c.name for c in obj.categories.all()[:5]) or "—"


class ProductAdminForm(forms.ModelForm):
    """
    Mahsulot formasida: brend tanlansa, kategoriya faqat o'sha brend
    kategoriyalaridan chiqadi (zanjirli). Bu server tomonda ham
    tekshiriladi (model.clean).
    """
    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agar brend tanlangan bo'lsa (tahrirlashda), kategoriyani chekla
        brand = None
        if self.instance and self.instance.pk:
            brand = self.instance.brand
        elif "brand" in self.data:
            try:
                brand = Brand.objects.get(pk=self.data.get("brand"))
            except (Brand.DoesNotExist, ValueError):
                brand = None
        if brand:
            self.fields["category"].queryset = brand.categories.all()


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("name", "brand", "category", "price", "unit",
                    "stock", "is_new", "is_promo", "is_active")
    list_filter = ("category", "brand", "is_new", "is_promo", "is_active")
    list_editable = ("price", "stock", "is_active")
    search_fields = ("name", "brand__name")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("brand",)
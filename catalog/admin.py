from django import forms
from django.contrib import admin
from .models import Category, Brand, Product


# ============================================================
# FORMA SOZLAMALARI (UI/UX VA DINAMIK FILTRLASH)
# ============================================================

class WideTextInputMixin:
    """Matnli maydonlarni to'liq kenglikka moslovchi yordamchi mixin."""
    def apply_wide_widgets(self):
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({
                    "style": "width: 100%; min-width: 450px; font-size: 14px; padding: 6px 10px;",
                })
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    "style": "width: 100%; min-width: 550px; font-size: 14px;",
                    "rows": 4,
                })


class WideTextInputForm(forms.ModelForm, WideTextInputMixin):
    """Kategoriya va Brend uchun kengaytirilgan forma."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_wide_widgets()


class ProductAdminForm(forms.ModelForm, WideTextInputMixin):
    """
    Mahsulot formasi:
    1. Maydonlarni to'liq kenglikka moslaydi.
    2. Agar brend tanlansa, kategoriyani faqat shu brendga tegishli qilib cheklaydi.
    """
    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_wide_widgets()

        # Brendga qarab kategoriyalar filtratsiyasi
        brand = None
        if self.instance and self.instance.pk:
            brand = getattr(self.instance, "brand", None)
        elif "brand" in self.data:
            try:
                brand = Brand.objects.get(pk=self.data.get("brand"))
            except (Brand.DoesNotExist, ValueError):
                brand = None

        if brand and hasattr(brand, "categories"):
            self.fields["category"].queryset = brand.categories.all()


# ============================================================
# ADMIN MODELLAR
# ============================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = WideTextInputForm
    list_display = ("id", "name", "get_parent", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")

    @admin.display(description="Asosiy kategoriya")
    def get_parent(self, obj):
        return getattr(obj, "parent", "—")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    form = WideTextInputForm
    list_display = ("id", "name", "categories_list", "get_is_official", "get_order", "is_active")
    list_filter = ("is_active",)
    list_editable = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # Agar Brand modelida 'categories' ManyToMany bo'lsa, horizontal filtr yoqiladi
        if hasattr(self.model, "categories"):
            self.filter_horizontal = ("categories",)

    @admin.display(description="Kategoriyalar")
    def categories_list(self, obj):
        if hasattr(obj, "categories"):
            return ", ".join(c.name for c in obj.categories.all()[:5]) or "—"
        return "—"

    @admin.display(description="Rasmiy brend", boolean=True)
    def get_is_official(self, obj):
        return getattr(obj, "is_official", False)

    @admin.display(description="Tartib")
    def get_order(self, obj):
        return getattr(obj, "order", 0)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        "id", "name", "brand", "category", "price", "unit",
        "get_status_label", "is_available_status"
    )
    list_filter = ("brand", "category")
    list_editable = ("price",)
    search_fields = ("name", "brand__name", "category__name")
    autocomplete_fields = ("brand",)
    save_on_top = True

    def get_readonly_fields(self, request, obj=None):
        # Mavjud bo'lgan vaqt belgilarini avtomatik readonly qilish
        fields = []
        if hasattr(self.model, "created_at"):
            fields.append("created_at")
        if hasattr(self.model, "updated_at"):
            fields.append("updated_at")
        return tuple(fields)

    @admin.display(description="Mavjudligi", boolean=True)
    def is_available_status(self, obj):
        # 1-koddagi is_available yoki 2-koddagi is_active ikkisini ham xatosiz o'qiydi
        return getattr(obj, "is_available", getattr(obj, "is_active", True))

    @admin.display(description="Yorliqlar")
    def get_status_label(self, obj):
        labels = []
        if getattr(obj, "is_new", False):
            labels.append("Yangi")
        if getattr(obj, "is_promo", False):
            labels.append("Aksiya")
        return ", ".join(labels) if labels else "—"
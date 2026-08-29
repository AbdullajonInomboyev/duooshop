from rest_framework import serializers
from .models import Category, Brand, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon"]


class BrandListSerializer(serializers.ModelSerializer):
    """Ro'yxat uchun yengil — faqat logo va nom."""
    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "logo", "is_official"]


class ProductListSerializer(serializers.ModelSerializer):
    """
    Ro'yxat uchun YENGIL serializer: thumbnail ishlatiladi, tavsif yo'q.
    Bu lazy loading + kam trafik tamoyilining bazadagi ifodasi.
    """
    category_name = serializers.CharField(source="category.name", read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "category_name", "price", "unit",
                  "image", "in_stock", "is_new", "is_promo"]

    def get_image(self, obj):
        # Ro'yxatda thumbnail bo'lsa o'shani, bo'lmasa to'liq rasmni.
        img = obj.thumbnail or obj.image
        if not img:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(img.url) if request else img.url


class ProductDetailSerializer(serializers.ModelSerializer):
    """Tafsilot uchun to'liq: to'liq rasm, tavsif, reyting."""
    brand = BrandListSerializer(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "brand", "category_name",
                  "price", "unit", "items_per_pack", "stock", "in_stock",
                  "min_order_qty", "image", "is_new", "is_promo", "rating"]

from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from .models import Category, Brand, Product
from .serializers import (
    CategorySerializer, BrandListSerializer,
    ProductListSerializer, ProductDetailSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Kategoriyalar ro'yxati (kam o'zgaradi, keshga mos)."""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    """Brendlar. ?category=<id> bilan filtrlanadi."""
    serializer_class = BrandListSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # brendlar kam, hammasi bir marta keladi
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        qs = Brand.objects.filter(is_active=True).prefetch_related("categories")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(categories__id=category)
        return qs.distinct()


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Mahsulotlar. ?brand= / ?category= filtrlari.
    Pagination yo'q — brend/kategoriya ichidagi hamma mahsulot bir marta keladi."""
    permission_classes = [AllowAny]
    pagination_class = None  # hamma mahsulot doim ko'rinadi (20 ta cheklov yo'q)
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "brand__name"]

    def get_queryset(self):
        qs = (Product.objects.filter(is_active=True)
              .select_related("brand", "category"))
        brand = self.request.query_params.get("brand")
        category = self.request.query_params.get("category")
        if brand:
            qs = qs.filter(brand_id=brand)
        if category:
            qs = qs.filter(category_id=category)
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer
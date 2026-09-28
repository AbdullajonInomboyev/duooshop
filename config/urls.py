"""
GoDostavka URL konfiguratsiyasi.

/admin/          -> Boshqaruv paneli (admin + sotuv bo'limi)
/api/            -> Mobil ilova uchun REST API
/media/          -> Yuklangan rasmlar (dev rejimida)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView,
)

from accounts.views import (
    RegionViewSet, DistrictViewSet, RegisterView, MeView,
)
from catalog.views import CategoryViewSet, BrandViewSet, ProductViewSet
from orders.views import CartView, OrderViewSet
from promotions.views import BannerViewSet, PromoScreenViewSet
from core.views import AppVersionView, SiteConfigView, FeedbackView
from orders.wagon_views import waybill_single, waybill_grouped, waybill_multiple, waybill_by_brand, waybill_selected_by_brand

router = DefaultRouter()
router.register("regions", RegionViewSet, basename="region")
router.register("districts", DistrictViewSet, basename="district")
router.register("categories", CategoryViewSet, basename="category")
router.register("brands", BrandViewSet, basename="brand")
router.register("products", ProductViewSet, basename="product")
router.register("orders", OrderViewSet, basename="order")
router.register("banners", BannerViewSet, basename="banner")
router.register("promo-screens", PromoScreenViewSet, basename="promo")

urlpatterns = [
    # Yuk xati (накладная) — admin.site.urls dan OLDIN turishi shart
    path("admin/waybill/order/<int:order_id>/", waybill_single, name="waybill-single"),
    path("admin/waybill/grouped/", waybill_grouped, name="waybill-grouped"),
    path("admin/waybill/multiple/", waybill_multiple, name="waybill-multiple"),
    path("admin/waybill/by-brand/", waybill_by_brand, name="waybill-by-brand"),
    path("admin/waybill/selected-by-brand/", waybill_selected_by_brand, name="waybill-selected-by-brand"),

    path("admin/", admin.site.urls),

    # Autentifikatsiya (telefon + parol -> JWT token)
    path("api/auth/login/", TokenObtainPairView.as_view(), name="login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/me/", MeView.as_view(), name="me"),

    # Savat (alohida, viewset emas)
    path("api/cart/", CartView.as_view(), name="cart"),

    # Majburiy yangilash
    path("api/core/app-version/", AppVersionView.as_view(), name="app-version"),
    path("api/core/config/", SiteConfigView.as_view(), name="site-config"),
    path("api/core/feedback/", FeedbackView.as_view(), name="feedback"),

    # Qolgan barcha resurslar
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
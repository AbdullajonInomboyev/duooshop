from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem, Order
from .serializers import (
    CartSerializer, OrderListSerializer, OrderDetailSerializer,
    CreateOrderSerializer,
)


def get_shop_or_403(request):
    shop = getattr(request.user, "shop", None)
    return shop


class CartView(APIView):
    """Do'konning savati: ko'rish, mahsulot qo'shish/o'chirish, miqdor."""

    def get(self, request):
        shop = get_shop_or_403(request)
        cart, _ = Cart.objects.get_or_create(shop=shop)
        return Response(CartSerializer(cart, context={"request": request}).data)

    def post(self, request):
        """{product, quantity} — qo'shadi yoki miqdorni yangilaydi."""
        from catalog.models import Product
        shop = get_shop_or_403(request)
        cart, _ = Cart.objects.get_or_create(shop=shop)
        product_id = request.data.get("product")
        quantity = int(request.data.get("quantity", 1))
        if quantity <= 0:
            CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        else:
            # Stock tekshiruvi: 0 bo'lsa "Qolmagan"
            product = Product.objects.filter(pk=product_id).first()
            if product is None:
                return Response({"detail": "Mahsulot topilmadi."},
                                status=status.HTTP_404_NOT_FOUND)
            if product.stock <= 0:
                return Response({"detail": "Mahsulot qolmagan."},
                                status=status.HTTP_400_BAD_REQUEST)
            CartItem.objects.update_or_create(
                cart=cart, product_id=product_id,
                defaults={"quantity": quantity},
            )
        return Response(CartSerializer(cart, context={"request": request}).data)

    def delete(self, request):
        """Savatni tozalash."""
        shop = get_shop_or_403(request)
        Cart.objects.filter(shop=shop).first().items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    """Buyurtmalar tarixi va chek. Do'kon faqat o'z buyurtmalarini ko'radi."""

    def get_queryset(self):
        shop = get_shop_or_403(self.request)
        return Order.objects.filter(shop=shop).prefetch_related("items")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderListSerializer

    def create(self, request):
        """Savatdan buyurtma rasmiylashtirish -> chek qaytadi."""
        shop = get_shop_or_403(request)
        ser = CreateOrderSerializer(data=request.data, context={"shop": shop})
        ser.is_valid(raise_exception=True)
        order = ser.save()
        return Response(
            OrderDetailSerializer(order, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="update-item")
    def update_item(self, request, pk=None):
        """
        Buyurtma mahsulotini tahrirlash yoki o'chirish.
        {item_id, quantity} — quantity=0 bo'lsa o'chiriladi.
        Faqat 'new' yoki 'confirmed' holatidagi buyurtmalar
        tahrirlanadi (yetkazilgan/to'langan emas). Yangi mahsulot
        qo'shib bo'lmaydi — faqat mavjudlarini o'zgartirish/o'chirish.
        """
        order = self.get_object()
        if order.status not in ("new", "confirmed"):
            return Response(
                {"detail": "Bu buyurtmani endi tahrirlab bo'lmaydi."},
                status=status.HTTP_400_BAD_REQUEST)

        item_id = request.data.get("item_id")
        quantity = int(request.data.get("quantity", 0))
        item = order.items.filter(pk=item_id).first()
        if item is None:
            return Response({"detail": "Mahsulot topilmadi."},
                            status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.line_total = item.unit_price * quantity
            item.save(update_fields=["quantity", "line_total"])

        # Jami summani qayta hisoblaymiz
        from django.db.models import Sum
        total = order.items.aggregate(s=Sum("line_total"))["s"] or 0
        order.items_total = total
        order.total = total
        order.save(update_fields=["items_total", "total"])

        # Agar hamma mahsulot o'chirilsa, buyurtmani bekor qilamiz
        if not order.items.exists():
            order.status = "cancelled"
            order.save(update_fields=["status"])

        return Response(
            OrderDetailSerializer(order, context={"request": request}).data)
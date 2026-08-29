from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from catalog.models import Product
from .models import Cart, CartItem, Order, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    price = serializers.DecimalField(source="product.price", max_digits=12,
                                     decimal_places=2, read_only=True)
    unit = serializers.CharField(source="product.unit", read_only=True)
    line_total = serializers.DecimalField(max_digits=14, decimal_places=2,
                                          read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_name", "price", "unit",
                  "quantity", "line_total"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items", "total"]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product_name", "unit_price", "quantity", "unit", "line_total"]


class OrderListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "receipt_number", "status", "status_display",
                  "total", "created_at"]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "receipt_number", "shop_name", "status", "status_display",
                  "payment_type", "items", "items_total", "delivery_fee",
                  "total", "created_at"]


class CreateOrderSerializer(serializers.Serializer):
    """
    Savatdan buyurtma yaratadi. Narxlarni nusxa qiladi, qoldiqni kamaytiradi,
    chek raqami avtomatik beriladi. Hammasi bitta tranzaksiyada.
    """
    payment_type = serializers.ChoiceField(
        choices=Order.PaymentType.choices, default=Order.PaymentType.CASH,
    )
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        shop = self.context["shop"]
        cart = getattr(shop, "cart", None)
        if not cart or not cart.items.exists():
            raise serializers.ValidationError("Savat bo'sh.")
        attrs["cart"] = cart
        return attrs

    @transaction.atomic
    def create(self, validated):
        shop = self.context["shop"]
        cart = validated["cart"]

        order = Order.objects.create(
            shop=shop,
            payment_type=validated["payment_type"],
            comment=validated.get("comment", ""),
            status=Order.Status.NEW,
        )

        items_total = Decimal("0")
        for ci in cart.items.select_related("product"):
            product = ci.product
            line = product.price * ci.quantity
            OrderItem.objects.create(
                order=order, product=product, product_name=product.name,
                unit_price=product.price, quantity=ci.quantity,
                unit=product.unit, line_total=line,
            )
            # Qoldiqni kamaytirish.
            product.stock = max(0, product.stock - ci.quantity)
            product.save(update_fields=["stock"])
            items_total += line

        order.items_total = items_total
        order.total = items_total + order.delivery_fee
        order.save(update_fields=["items_total", "total"])

        # Nasiya bo'lsa do'kon qarzini oshirish.
        if order.payment_type == Order.PaymentType.CREDIT:
            shop.debt_balance += order.total
            shop.save(update_fields=["debt_balance"])

        # Savatni tozalash.
        cart.items.all().delete()
        return order

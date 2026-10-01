"""
orders — Savat, buyurtma, chek va to'lovlar tizimi.

- Cart/CartItem: Do'kon egasining savati (serverda saqlanadi).
- Order/OrderItem: Rasmiylashtirilgan buyurtma, qat'iy chek raqami (SHT-YYYYMMDD-NNNN).
- Tarixiy fiksatsiya: OrderItem'da mahsulot nomi, narxi va o'lchov birligi qotiriladi.
- Payment: B2B qarz/nasiya va to'lovlar harakati jurnali.
"""
from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from accounts.models import Shop, User
from catalog.models import Product


# ============================================================
# SAVAT (CART)
# ============================================================

class Cart(models.Model):
    """Do'konning joriy savati. Bitta do'konga bitta faol savat."""
    shop = models.OneToOneField(
        Shop,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name=_("Do'kon"),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan vaqti"))

    class Meta:
        verbose_name = _("Savat")
        verbose_name_plural = _("Savatlar")

    @property
    def total(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))

    # 1-kod bilan moslik (total_amount deb murojaat qilinganda xato bermasligi uchun)
    @property
    def total_amount(self):
        return self.total

    def __str__(self):
        return f"Savat — {self.shop.name}"


class CartItem(models.Model):
    """Savatchadagi mahsulot pozitsiyalari."""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Savat"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name=_("Mahsulot"),
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Miqdor"))

    class Meta:
        verbose_name = _("Savat elementi")
        verbose_name_plural = _("Savat elementlari")
        unique_together = ("cart", "product")

    @property
    def line_total(self):
        return Decimal(str(self.product.price)) * Decimal(self.quantity)

    # 1-kod bilan moslik (total_price deb murojaat qilinganda)
    @property
    def total_price(self):
        return self.line_total

    def __str__(self):
        return f"{self.product.name} ({self.quantity} dona)"


# ============================================================
# BUYURTMA (ORDER)
# ============================================================

class Order(models.Model):
    """Rasmiylashtirilgan buyurtma."""

    class Status(models.TextChoices):
        NEW = "new", _("Yangi")
        CONFIRMED = "confirmed", _("Tasdiqlandi")
        PACKED = "packed", _("Yig'ildi")
        ON_THE_WAY = "on_the_way", _("Yo'lda")
        DELIVERED = "delivered", _("Yetkazildi")
        PAID = "paid", _("To'landi")
        CANCELLED = "cancelled", _("Bekor qilindi")

    class PaymentType(models.TextChoices):
        CASH = "cash", _("Naqd pul")
        CREDIT = "credit", _("Nasiya")
        TRANSFER = "transfer", _("O'tkazma")

    receipt_number = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        blank=True,
        verbose_name=_("Chek raqami"),
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name=_("Do'kon"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Buyurtma beruvchi"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
        verbose_name=_("Holat"),
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.CASH,
        verbose_name=_("To'lov turi"),
    )

    # Moliyaviy fiksatsiyalar
    items_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Mahsulotlar summasi"),
    )
    delivery_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Yetkazib berish"),
    )
    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Chegirma summasi"),
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Jami summa"),
    )

    courier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
        verbose_name=_("Dastavkachi"),
        limit_choices_to={"role": getattr(getattr(User, "Role", None), "COURIER", "courier")},
    )
    comment = models.TextField(blank=True, verbose_name=_("Izoh"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan sana"))
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Tasdiqlangan vaqt"))
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Yetkazilgan vaqt"))
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name=_("To'langan vaqt"))

    class Meta:
        verbose_name = _("Buyurtma")
        verbose_name_plural = _("Buyurtmalar")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["shop", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["receipt_number"]),
        ]

    # 1-kod bilan moslik property'lari
    @property
    def order_number(self):
        return self.receipt_number

    @property
    def final_amount(self):
        return self.total

    @property
    def note(self):
        return self.comment

    def generate_receipt_number(self):
        """SHT-YYYYMMDD-NNNN formati (poyga holatiga qarshi tranzaksiya bilan)."""
        today = timezone.now().strftime("%Y%m%d")
        prefix = f"SHT-{today}-"
        with transaction.atomic():
            last = (
                Order.objects.select_for_update()
                .filter(receipt_number__startswith=prefix)
                .order_by("-receipt_number")
                .first()
            )
            seq = int(last.receipt_number.split("-")[-1]) + 1 if last else 1
            return f"{prefix}{seq:04d}"

    def recalculate_totals(self, save=True):
        """Buyurtma qatorlaridagi o'zgarmas narxlar bo'yicha summani hisoblash."""
        items_sum = sum(item.line_total for item in self.items.all())
        self.items_total = items_sum
        self.total = max(Decimal("0.00"), items_sum + self.delivery_fee - self.discount_amount)
        if save:
            self.save(update_fields=["items_total", "total", "updated_at"])

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number


# ============================================================
# BUYURTMA QATORI (ORDER ITEM)
# ============================================================

class OrderItem(models.Model):
    """
    Buyurtma qatori. Mahsulot nomi va narxi NUSXA qilib saqlanadi —
    keyin mahsulot o'zgarsa ham chek o'zgarmaydi.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Buyurtma"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        null=True,
        related_name="order_items",
        verbose_name=_("Mahsulot"),
    )
    product_name = models.CharField(max_length=250, verbose_name=_("Mahsulot nomi"))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Dona narxi"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Miqdor"))
    unit = models.CharField(max_length=10, blank=True, verbose_name=_("O'lchov birligi"))
    line_total = models.DecimalField(max_digits=14, decimal_places=2, verbose_name=_("Qator summasi"))

    class Meta:
        verbose_name = _("Buyurtma qatori")
        verbose_name_plural = _("Buyurtma qatorlari")

    # 1-kod bilan moslik
    @property
    def total_price(self):
        return self.line_total

    def save(self, *args, **kwargs):
        # 1. Narx berilmagan bo'lsa, katalogdagi joriy narx bilan to'ldiramiz
        if self.unit_price is None and self.product:
            self.unit_price = self.product.price

        # 2. Mahsulot nomi va o'lchov birligini fiksatsiya qilamiz
        if not self.product_name and self.product:
            self.product_name = self.product.name
        if not self.unit and self.product and hasattr(self.product, "unit"):
            self.unit = str(self.product.unit)

        # 3. Qator summasi doim: unit_price * quantity
        if self.unit_price is not None:
            self.line_total = Decimal(str(self.unit_price)) * Decimal(self.quantity)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x {self.quantity} = {self.line_total} so'm"


# ============================================================
# TO'LOV VA NASIYA (PAYMENT)
# ============================================================

class Payment(models.Model):
    """
    Nasiya to'lovlari. Do'kon qarzini to'laganda shu yerga yoziladi,
    do'konning debt_balance kamayadi. Buxgalteriya uchun asosiy jurnal.
    """
    shop = models.ForeignKey(
        Shop,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name=_("Do'kon"),
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name=_("Buyurtma"),
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2, verbose_name=_("Summa"))
    note = models.CharField(max_length=255, blank=True, verbose_name=_("Izoh"))
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_payments",
        verbose_name=_("Qabul qildi"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("To'lov vaqti"))

    class Meta:
        verbose_name = _("To'lov")
        verbose_name_plural = _("To'lovlar")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.shop.name}: {self.amount}"
"""
orders — savat, buyurtma va chek.

- Cart/CartItem: do'kon egasining savati (server tomonda saqlanadi).
- Order/OrderItem: rasmiylashtirilgan buyurtma. Har biriга chek raqami beriladi.
- Chek raqami formati: SHT-YYYYMMDD-NNNN (dizayndagi bilan bir xil).
- OrderItem'da narx VA nom nusxa qilib saqlanadi: keyin mahsulot narxi
  o'zgarsa ham, eski chek o'zgarmaydi (buxgalteriya to'g'ri bo'lishi uchun).
- Buyurtma statuslari: yangi -> tasdiqlandi -> yig'ildi -> yo'lda ->
  yetkazildi -> to'landi (yoki bekor qilindi).
"""
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import Shop, User
from catalog.models import Product


class Cart(models.Model):
    """Do'konning joriy savati. Bitta do'konga bitta faol savat."""
    shop = models.OneToOneField(
        Shop, on_delete=models.CASCADE, related_name="cart",
        verbose_name=_("Do'kon"),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Savat")
        verbose_name_plural = _("Savatlar")

    @property
    def total(self):
        return sum((i.line_total for i in self.items.all()), Decimal("0"))

    def __str__(self):
        return f"Savat — {self.shop.name}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(_("Miqdor"), default=1)

    class Meta:
        verbose_name = _("Savat elementi")
        verbose_name_plural = _("Savat elementlari")
        unique_together = ("cart", "product")

    @property
    def line_total(self):
        return self.product.price * self.quantity


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
        _("Chek raqami"), max_length=30, unique=True, db_index=True, blank=True,
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.PROTECT, related_name="orders",
        verbose_name=_("Do'kon"),
    )
    status = models.CharField(
        _("Holat"), max_length=20, choices=Status.choices, default=Status.NEW,
        db_index=True,
    )
    payment_type = models.CharField(
        _("To'lov turi"), max_length=20, choices=PaymentType.choices,
        default=PaymentType.CASH,
    )

    # Yig'indilar — buyurtma paytida qotirib saqlanadi.
    items_total = models.DecimalField(
        _("Mahsulotlar summasi"), max_digits=14, decimal_places=2, default=0,
    )
    delivery_fee = models.DecimalField(
        _("Yetkazib berish"), max_digits=12, decimal_places=2, default=0,
    )
    total = models.DecimalField(
        _("Jami summa"), max_digits=14, decimal_places=2, default=0,
    )

    courier = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="deliveries", verbose_name=_("Dastavkachi"),
        limit_choices_to={"role": User.Role.COURIER},
    )
    comment = models.TextField(_("Izoh"), blank=True)

    created_at = models.DateTimeField(_("Yaratilgan sana"), auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Buyurtma")
        verbose_name_plural = _("Buyurtmalar")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["shop", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def generate_receipt_number(self):
        """SHT-YYYYMMDD-NNNN — kun ichidagi tartib raqami bilan."""
        today = timezone.now().strftime("%Y%m%d")
        prefix = f"SHT-{today}-"
        last = (
            Order.objects.filter(receipt_number__startswith=prefix)
            .order_by("-receipt_number").first()
        )
        seq = int(last.receipt_number.split("-")[-1]) + 1 if last else 1
        return f"{prefix}{seq:04d}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number


class OrderItem(models.Model):
    """
    Buyurtma qatori. Mahsulot nomi va narxi NUSXA qilib saqlanadi —
    keyin mahsulot o'zgarsa ham chek o'zgarmaydi.
    """
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items",
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Mahsulot"),
    )
    product_name = models.CharField(_("Mahsulot nomi"), max_length=250)
    unit_price = models.DecimalField(_("Dona narxi"), max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(_("Miqdor"))
    unit = models.CharField(_("O'lchov birligi"), max_length=10, blank=True)
    line_total = models.DecimalField(_("Qator summasi"), max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = _("Buyurtma qatori")
        verbose_name_plural = _("Buyurtma qatorlari")


class Payment(models.Model):
    """
    Nasiya to'lovlari. Do'kon qarzini to'laganda shu yerga yoziladi,
    do'konning debt_balance kamayadi. Buxgalteriya uchun asosiy jurnal.
    """
    shop = models.ForeignKey(
        Shop, on_delete=models.PROTECT, related_name="payments",
        verbose_name=_("Do'kon"),
    )
    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="payments", verbose_name=_("Buyurtma"),
    )
    amount = models.DecimalField(_("Summa"), max_digits=14, decimal_places=2)
    note = models.CharField(_("Izoh"), max_length=255, blank=True)
    received_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Qabul qildi"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("To'lov")
        verbose_name_plural = _("To'lovlar")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.shop.name}: {self.amount}"

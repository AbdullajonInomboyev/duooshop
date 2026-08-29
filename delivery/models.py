"""
delivery — dastavka (yetkazib berish) moduli.

2-bosqichda dastavkachi ilovasi bilan to'liq ishlatiladi. Hozir model
tayyor turadi: buyurtma dastavkachiga biriktiriladi, marshrut va
yetkazish holati shu yerda kuzatiladi.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from orders.models import Order


class DeliveryRoute(models.Model):
    """Dastavkachining bir kunlik marshruti (buyurtmalar to'plami)."""
    courier = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="routes",
        limit_choices_to={"role": User.Role.COURIER},
        verbose_name=_("Dastavkachi"),
    )
    date = models.DateField(_("Sana"))
    is_closed = models.BooleanField(_("Yopilgan"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Marshrut")
        verbose_name_plural = _("Marshrutlar")
        ordering = ["-date"]
        unique_together = ("courier", "date")

    def __str__(self):
        return f"{self.courier.full_name} — {self.date}"


class DeliveryStop(models.Model):
    """Marshrutdagi bitta to'xtash — bitta buyurtmani yetkazish."""
    route = models.ForeignKey(
        DeliveryRoute, on_delete=models.CASCADE, related_name="stops",
    )
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="delivery_stop",
        verbose_name=_("Buyurtma"),
    )
    sequence = models.PositiveIntegerField(_("Tartib"), default=0)
    is_delivered = models.BooleanField(_("Yetkazildi"), default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    collected_amount = models.DecimalField(
        _("Yig'ilgan pul"), max_digits=14, decimal_places=2, default=0,
    )
    note = models.CharField(_("Izoh"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Yetkazish nuqtasi")
        verbose_name_plural = _("Yetkazish nuqtalari")
        ordering = ["sequence"]

    def __str__(self):
        return f"{self.order.receipt_number} — {self.order.shop.name}"

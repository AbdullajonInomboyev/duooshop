"""
accounts — foydalanuvchilar va hududlar.

Bu yerda tizimning barcha odamlari (do'kon egasi, dastavkachi, sotuvchi,
buxgalter, admin) va geografik bo'linish (viloyat, tuman) saqlanadi.
Respublika miqyosi uchun hudud modeli boshidanoq kiritilgan.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Region(models.Model):
    """Viloyat. Har bir do'kon va sklad bittasiga bog'lanadi."""
    name = models.CharField(_("Viloyat nomi"), max_length=100, unique=True)
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        verbose_name = _("Viloyat")
        verbose_name_plural = _("Viloyatlar")
        ordering = ["name"]

    def __str__(self):
        return self.name


class District(models.Model):
    """Tuman — viloyat ichida."""
    region = models.ForeignKey(
        Region, on_delete=models.CASCADE, related_name="districts",
        verbose_name=_("Viloyat"),
    )
    name = models.CharField(_("Tuman nomi"), max_length=100)
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        verbose_name = _("Tuman")
        verbose_name_plural = _("Tumanlar")
        ordering = ["region__name", "name"]
        unique_together = ("region", "name")

    def __str__(self):
        return f"{self.region.name} — {self.name}"


class User(AbstractUser):
    """
    Umumiy foydalanuvchi. `role` orqali kim ekani aniqlanadi.
    Telefon raqam — asosiy identifikator (do'kon egasi telefon bilan kiradi).
    """

    class Role(models.TextChoices):
        SHOP = "shop", _("Do'kon egasi")
        COURIER = "courier", _("Dastavkachi")
        SALES = "sales", _("Sotuvchi")
        ACCOUNTANT = "accountant", _("Buxgalter")
        ADMIN = "admin", _("Administrator")

    role = models.CharField(
        _("Rol"), max_length=20, choices=Role.choices, default=Role.SHOP,
    )
    phone = models.CharField(_("Telefon raqam"), max_length=20, unique=True)
    full_name = models.CharField(_("Ism familiya"), max_length=150, blank=True)

    region = models.ForeignKey(
        "accounts.Region", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="staff", verbose_name=_("Biriktirilgan viloyat"),
    )
    push_token = models.CharField(_("Push token"), max_length=255, blank=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")

    def __str__(self):
        return f"{self.full_name or self.username} ({self.get_role_display()})"


def shop_logo_path(instance, filename):
    return f"shops/{instance.pk or 'new'}/{filename}"


class Shop(models.Model):
    """
    Do'kon — do'kon egasining biznesi. Bitta foydalanuvchiga bitta do'kon.
    Tasdiqlash yo'q: ro'yxatdan o'tdi -> darhol faol.
    """
    owner = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="shop",
        verbose_name=_("Egasi"),
    )
    name = models.CharField(_("Do'kon nomi"), max_length=200)
    image = models.ImageField(
        _("Do'kon rasmi"), upload_to=shop_logo_path, null=True, blank=True,
    )
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="shops",
        verbose_name=_("Viloyat"),
    )
    district = models.ForeignKey(
        District, on_delete=models.PROTECT, related_name="shops",
        verbose_name=_("Tuman"),
    )
    latitude = models.DecimalField(
        _("Kenglik"), max_digits=9, decimal_places=6, null=True, blank=True,
    )
    longitude = models.DecimalField(
        _("Uzunlik"), max_digits=9, decimal_places=6, null=True, blank=True,
    )
    address_text = models.CharField(_("Manzil (matn)"), max_length=255, blank=True)

    debt_balance = models.DecimalField(
        _("Qarz balansi"), max_digits=14, decimal_places=2, default=0,
    )
    credit_limit = models.DecimalField(
        _("Nasiya limiti"), max_digits=14, decimal_places=2, default=0,
        help_text=_("Do'kon ko'pi bilan qancha qarzga ola oladi. 0 = limitsiz."),
    )

    is_active = models.BooleanField(_("Faol"), default=True)
    is_new = models.BooleanField(
        _("Yangi"), default=True,
        help_text=_("Admin/dastavkachi hali ko'rmagan yangi do'kon."),
    )
    created_at = models.DateTimeField(_("Ro'yxatdan o'tgan sana"), auto_now_add=True)

    class Meta:
        verbose_name = _("Do'kon")
        verbose_name_plural = _("Do'konlar")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["region", "district"]),
            models.Index(fields=["is_new"]),
        ]

    def __str__(self):
        return self.name

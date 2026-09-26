"""
core — tizim sozlamalari, jumladan majburiy yangilash (force update).

Ilova har ochilganda /api/core/app-version/ ni so'raydi. Agar ilova
versiyasi min_version dan past bo'lsa, oldiga to'siq ekran chiqadi va
foydalanuvchini yangilashga majbur qiladi (ilovaga kirgizmaydi).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class AppVersion(models.Model):
    """Har platforma uchun eng oxirgi va minimal kerakli versiya."""

    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    platform = models.CharField(
        _("Platforma"), max_length=10, choices=Platform.choices, unique=True,
    )
    latest_version = models.CharField(_("Oxirgi versiya"), max_length=20)
    min_version = models.CharField(
        _("Minimal kerakli versiya"), max_length=20,
        help_text=_("Bundan past versiyalar majburiy yangilanadi."),
    )
    store_url = models.URLField(_("Do'kon havolasi (Play/App Store)"), blank=True)
    apk_file = models.FileField(
        _("APK fayl (Android)"), upload_to="apk/", blank=True, null=True,
        help_text=_("Android APK faylini shu yerga yuklang. "
                    "Foydalanuvchi 'Yangilash' bosganda shundan yuklab oladi."),
    )
    release_notes = models.TextField(_("Yangiliklar"), blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Ilova versiyasi")
        verbose_name_plural = _("Ilova versiyalari")

    def __str__(self):
        return f"{self.get_platform_display()} — {self.latest_version}"


class SiteConfig(models.Model):
    """
    Umumiy sozlamalar (bitta yozuv). Masalan admin telefon raqami —
    do'kon egasi tasdiqlash uchun bog'lanadi.
    """
    admin_phone = models.CharField(
        _("Admin telefon raqami"), max_length=20, blank=True,
        help_text=_("Tasdiqlash uchun do'kon egasi shu raqamga bog'lanadi."),
    )
    admin_name = models.CharField(
        _("Admin ismi"), max_length=100, blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Sozlama")
        verbose_name_plural = _("Sozlamalar")

    def __str__(self):
        return "Umumiy sozlamalar"

    def save(self, *args, **kwargs):
        self.pk = 1  # har doim bitta yozuv (singleton)
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

class Feedback(models.Model):
    """
    Do'kon egasidan kelgan fikr/taklif. Ilovadan yuboriladi.
    Admin panelda o'qiladi — ilovani yaxshilash va qaysi mahsulotga
    ehtiyoj borligini bilish uchun.
    """
    shop = models.ForeignKey(
        "accounts.Shop", on_delete=models.CASCADE, related_name="feedbacks",
        verbose_name=_("Do'kon"), null=True, blank=True,
    )
    shop_name = models.CharField(_("Do'kon nomi"), max_length=200, blank=True)
    phone = models.CharField(_("Telefon"), max_length=20, blank=True)
    message = models.TextField(_("Fikr / taklif"))
    is_read = models.BooleanField(_("O'qilgan"), default=False)
    created_at = models.DateTimeField(_("Sana"), auto_now_add=True)

    class Meta:
        verbose_name = _("Fikr va taklif")
        verbose_name_plural = _("Fikr va takliflar")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.shop_name or 'Nomalum'} — {self.created_at:%d.%m.%Y}"
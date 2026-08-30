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
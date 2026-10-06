"""
promotions — reklama, banner va splash reklama.

Bularning hammasi admin paneldan boshqariladi. Ilova ochilganda
serverdan keladi -> ilovani yangilamay, darhol hamma do'konga ko'rinadi.
Rasm faqat kerak bo'lganda (ko'rsatilganda) yuklanadi.
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Banner(models.Model):
    """Bosh sahifadagi aylanuvchi bannerlar.
    Rasm BILAN yoki rasmSIZ (faqat matn) bo'lishi mumkin.
    Rasm bo'lmasa — sarlavha + tavsif matn, fon rangi bilan ko'rsatiladi."""
    title = models.CharField(_("Sarlavha"), max_length=200, blank=True)
    subtitle = models.CharField(
        _("Tavsif (matn banner uchun)"), max_length=300, blank=True,
        help_text=_("Rasm bo'lmaganda ko'rinadigan qo'shimcha matn."),
    )
    image = models.ImageField(
        _("Rasm"), upload_to="banners/", null=True, blank=True,
        help_text=_("Ixtiyoriy. Bo'sh qoldirilsa, matn banner ko'rsatiladi."),
    )
    bg_color = models.CharField(
        _("Fon rangi (matn banner)"), max_length=7, blank=True, default="#009D4D",
        help_text=_("Rasm bo'lmaganda fon rangi. Masalan: #009D4D"),
    )
    # Bosilganda qayerga o'tsin (ixtiyoriy: brend yoki mahsulot).
    link_type = models.CharField(
        _("Havola turi"), max_length=20, blank=True,
        choices=[("brand", "Brend"), ("product", "Mahsulot"), ("url", "URL")],
    )
    link_value = models.CharField(_("Havola qiymati"), max_length=255, blank=True)
    order = models.PositiveIntegerField(_("Tartib"), default=0)
    is_active = models.BooleanField(_("Faol"), default=True)
    starts_at = models.DateTimeField(_("Boshlanish"), null=True, blank=True)
    ends_at = models.DateTimeField(_("Tugash"), null=True, blank=True)

    class Meta:
        verbose_name = _("Banner")
        verbose_name_plural = _("Bannerlar")
        ordering = ["order"]

    def __str__(self):
        return self.title or f"Banner #{self.pk}"


class PromoScreen(models.Model):
    """
    Splash/interstitial reklama — kirishdan oldin yoki ilovaga
    kirgandan keyin bir marta chiqadigan to'liq ekranli reklama
    (Yandex uslubidagi). Rasm bilan yoki matn bilan.
    """
    class Placement(models.TextChoices):
        BEFORE_LOGIN = "before_login", _("Kirishdan oldin")
        AFTER_LOGIN = "after_login", _("Kirgandan keyin")

    title = models.CharField(_("Sarlavha"), max_length=200, blank=True)
    body = models.TextField(_("Matn"), blank=True)
    image = models.ImageField(_("Rasm"), upload_to="promos/", null=True, blank=True)
    placement = models.CharField(
        _("Joylashuv"), max_length=20, choices=Placement.choices,
        default=Placement.AFTER_LOGIN,
    )
    # Necha soniyadan keyin "×" chiqsin.
    skip_after_seconds = models.PositiveIntegerField(_("Skip (soniya)"), default=3)
    is_active = models.BooleanField(_("Faol"), default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Reklama ekrani")
        verbose_name_plural = _("Reklama ekranlari")

    def is_live(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    def __str__(self):
        return self.title or f"Promo #{self.pk}"
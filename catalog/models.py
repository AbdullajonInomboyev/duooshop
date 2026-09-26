"""
catalog — mahsulotlar katalogi: Kategoriya -> Brend -> Mahsulot.

Struktura:
- Kategoriya asosiy (Pechenye, Shokolad, Suv...).
- Brend bir yoki bir nechta kategoriyaga tegishli (ManyToMany).
  Masalan HydroLife faqat "Suv"da; Navroz ham "Pechenye" ham "Shokolad"da.
- Mahsulot: kategoriya + brend belgilanadi. Mahsulotning kategoriyasi
  brendning kategoriyalaridan biri bo'lishi shart (validatsiya).
  Shunda brend 2 kategoriyada bo'lsa ham, har kategoriyada FAQAT
  o'sha kategoriyaga tegishli mahsuloti ko'rinadi.

Masshtab uchun: baza yengil (matn + rasm manzillari), indekslar, thumbnail.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class Category(models.Model):
    """Bo'lim: masalan Pechenye, Shokolad, Suv, Kolbasa."""
    name = models.CharField(_("Kategoriya nomi"), max_length=120, unique=True)
    slug = models.SlugField(_("Slug"), max_length=140, unique=True, blank=True)
    icon = models.ImageField(
        _("Ikonka"), upload_to="categories/icons/", null=True, blank=True,
    )
    order = models.PositiveIntegerField(_("Tartib"), default=0)
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        verbose_name = _("Kategoriya")
        verbose_name_plural = _("Kategoriyalar")
        ordering = ["order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    """
    Brend: masalan Navroz, Coca-Cola, HydroLife.
    Bir yoki bir nechta kategoriyaga tegishli (ManyToMany).
    """
    name = models.CharField(_("Brend nomi"), max_length=150, unique=True)
    slug = models.SlugField(_("Slug"), max_length=170, unique=True, blank=True)
    categories = models.ManyToManyField(
        Category, related_name="brands", verbose_name=_("Kategoriyalar"),
        help_text=_("Bu brend qaysi kategoriyalarga tegishli (bir yoki bir nechta)."),
    )
    logo = models.ImageField(
        _("Brend logotipi"), upload_to="brands/logos/", null=True, blank=True,
    )
    is_official = models.BooleanField(_("Rasmiy distribyutor"), default=False)
    order = models.PositiveIntegerField(_("Tartib"), default=0)
    is_active = models.BooleanField(_("Faol"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Brend")
        verbose_name_plural = _("Brendlar")
        ordering = ["order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Unit(models.TextChoices):
    DONA = "dona", _("dona")
    BLOK = "blok", _("blok")
    KARTON = "karton", _("karton")
    KG = "kg", _("kg")
    LITR = "litr", _("litr")
    QOP = "qop", _("qop")


class Product(models.Model):
    """
    Mahsulot. Kategoriya + brend belgilanadi.
    Mahsulot kategoriyasi brend kategoriyalaridan biri bo'lishi shart.
    """
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="products",
        verbose_name=_("Brend"),
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products",
        verbose_name=_("Kategoriya"),
    )
    name = models.CharField(_("Mahsulot nomi"), max_length=250)
    description = models.TextField(_("Tavsif"), blank=True)

    image = models.ImageField(
        _("To'liq rasm"), upload_to="products/full/", null=True, blank=True,
    )
    thumbnail = models.ImageField(
        _("Kichik rasm (thumbnail)"), upload_to="products/thumbs/",
        null=True, blank=True,
        help_text=_("Ro'yxatda ishlatiladi."),
    )

    price = models.DecimalField(_("Narxi"), max_digits=12, decimal_places=2)
    unit = models.CharField(
        _("O'lchov birligi"), max_length=10, choices=Unit.choices,
        default=Unit.DONA,
    )
    items_per_pack = models.PositiveIntegerField(_("Qadoqdagi dona soni"), default=1)
    min_order_qty = models.PositiveIntegerField(_("Minimal zakaz miqdori"), default=1)

    is_new = models.BooleanField(_("Yangi"), default=False)
    is_promo = models.BooleanField(_("Aksiya"), default=False)
    rating = models.DecimalField(_("Reyting"), max_digits=2, decimal_places=1, default=0)

    is_active = models.BooleanField(_("Faol"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Mahsulot")
        verbose_name_plural = _("Mahsulotlar")
        ordering = ["name"]  # alfavit tartibida (A->Z)
        indexes = [
            models.Index(fields=["brand", "is_active"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["brand", "category", "is_active"]),
            models.Index(fields=["name"]),
        ]

    def clean(self):
        # Mahsulot kategoriyasi brend kategoriyalaridan biri bo'lishi shart.
        if self.brand_id and self.category_id:
            if not self.brand.categories.filter(pk=self.category_id).exists():
                raise ValidationError({
                    "category": _("Bu kategoriya tanlangan brendga tegishli emas. "
                                  "Avval brendga ushbu kategoriyani qo'shing.")
                })

    @property
    def in_stock(self):
        # Ombor doim to'la — hamma mahsulot doimo mavjud
        return True

    def __str__(self):
        return f"{self.name} ({self.brand.name})"
"""
catalog — mahsulotlar katalogi: Kategoriya -> Brend -> Mahsulot.

Muhim tamoyil (respublika miqyosi uchun):
- Baza YENGIL bo'ladi: bu yerda faqat matn va rasm MANZILLARI turadi.
- Rasmning o'zi ImageField orqali alohida omborda (media/CDN) saqlanadi.
- Ro'yxatda thumbnail (yengil), tafsilotda to'liq rasm ishlatiladi (lazy loading).
- Tez qidiriladigan maydonlarga (brend, kategoriya, nom) indeks qo'yilgan.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class Category(models.Model):
    """Bo'lim: masalan Ichimliklar, Shokolad, Kolbasa, Qurilish mollari."""
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
    Brend: masalan Navroz, Coca-Cola, Makfa.
    Brend bir yoki bir nechta kategoriyaga tegishli bo'lishi mumkin,
    lekin soddalik uchun asosiy kategoriyaga bog'laymiz.
    """
    name = models.CharField(_("Brend nomi"), max_length=150, unique=True)
    slug = models.SlugField(_("Slug"), max_length=170, unique=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="brands",
        verbose_name=_("Kategoriya"),
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
        indexes = [models.Index(fields=["category", "is_active"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Unit(models.TextChoices):
    """O'lchov birligi — ulgurjida muhim."""
    DONA = "dona", _("dona")
    BLOK = "blok", _("blok")
    KARTON = "karton", _("karton")
    KG = "kg", _("kg")
    LITR = "litr", _("litr")
    QOP = "qop", _("qop")


class Product(models.Model):
    """
    Mahsulot. Baza yengil: rasm manzillari (thumbnail + full) va matn.
    Narx va qoldiq shu yerda. Qoldiq 0 bo'lsa -> zakaz berib bo'lmaydi.
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

    # Ikki xil rasm: ro'yxat uchun yengil thumbnail, tafsilot uchun to'liq.
    image = models.ImageField(
        _("To'liq rasm"), upload_to="products/full/", null=True, blank=True,
    )
    thumbnail = models.ImageField(
        _("Kichik rasm (thumbnail)"), upload_to="products/thumbs/",
        null=True, blank=True,
        help_text=_("Ro'yxatda ishlatiladi. Yuklashda avtomatik yaratiladi."),
    )

    price = models.DecimalField(_("Narxi"), max_digits=12, decimal_places=2)
    unit = models.CharField(
        _("O'lchov birligi"), max_length=10, choices=Unit.choices,
        default=Unit.DONA,
    )
    # Blok/karton ichida nechta dona borligi (ixtiyoriy, hisob uchun).
    items_per_pack = models.PositiveIntegerField(
        _("Qadoqdagi dona soni"), default=1,
    )

    stock = models.IntegerField(_("Ombordagi qoldiq"), default=0)
    min_order_qty = models.PositiveIntegerField(_("Minimal zakaz miqdori"), default=1)

    is_new = models.BooleanField(_("Yangi"), default=False)
    is_promo = models.BooleanField(_("Aksiya"), default=False)
    rating = models.DecimalField(
        _("Reyting"), max_digits=2, decimal_places=1, default=0,
    )

    is_active = models.BooleanField(_("Faol"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Mahsulot")
        verbose_name_plural = _("Mahsulotlar")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["brand", "is_active"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["name"]),
        ]

    @property
    def in_stock(self):
        return self.stock > 0

    def __str__(self):
        return f"{self.name} ({self.brand.name})"

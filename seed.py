"""Namuna ma'lumot — API'ni tekshirish uchun."""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from accounts.models import Region, District, User
from catalog.models import Category, Brand, Product
from core.models import AppVersion

# Hududlar
tosh, _ = Region.objects.get_or_create(name="Toshkent")
farg, _ = Region.objects.get_or_create(name="Farg'ona")
d1, _ = District.objects.get_or_create(region=tosh, name="Chilonzor")
d2, _ = District.objects.get_or_create(region=tosh, name="Yunusobod")

# Kategoriya + brend + mahsulot
ich, _ = Category.objects.get_or_create(name="Ichimliklar", order=1)
un, _ = Category.objects.get_or_create(name="Un mahsulotlari", order=2)

cola, _ = Brand.objects.get_or_create(name="Coca-Cola", category=ich, is_official=True)
makfa, _ = Brand.objects.get_or_create(name="Makfa", category=un)

Product.objects.get_or_create(
    name="Coca-Cola Classic 1.5L PET", brand=cola, category=ich,
    defaults={"price": 9000, "unit": "dona", "stock": 500, "is_new": True,
              "description": "Sifatli va mazali gazli ichimlik."})
Product.objects.get_or_create(
    name="Fanta Apelsin 1.5L PET", brand=cola, category=ich,
    defaults={"price": 9000, "unit": "dona", "stock": 300})
Product.objects.get_or_create(
    name="Makfa un 2kg", brand=makfa, category=un,
    defaults={"price": 22000, "unit": "dona", "stock": 200})

# Versiya
AppVersion.objects.get_or_create(
    platform="android",
    defaults={"latest_version": "1.2.0", "min_version": "1.0.0",
              "store_url": "https://play.google.com/store/apps/details?id=uz.godostavka"})

# Test do'kon egasi
if not User.objects.filter(phone="+998901234567").exists():
    from accounts.models import Shop
    u = User.objects.create_user(username="+998901234567", phone="+998901234567",
                                 full_name="Ali Valiyev", password="1234",
                                 role="shop", region=tosh)
    Shop.objects.create(owner=u, name="Ali Market", region=tosh, district=d1)

# Superuser (admin panel uchun)
if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser(username="admin", phone="+998900000000",
                                  password="admin123", role="admin")

print("Seed tayyor. Do'konlar:", User.objects.filter(role='shop').count(),
      "| Mahsulotlar:", Product.objects.count())

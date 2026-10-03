"""
GoDostavka (DUOO) — B2B ulgurji savdo tizimi.
Django sozlamalari (Production va Development uchun moslashtirilgan).
"""
import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# Loyihaning asosiy papkasi
BASE_DIR = Path(__file__).resolve().parent.parent

# Xavfsizlik kaliti va Debug rejimi
SECRET_KEY = config("SECRET_KEY", default="django-insecure-duooshop-development-key-change-in-prod")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

# ============================================================
# INSTALLED APPS
# ============================================================
INSTALLED_APPS = [
    # Jazzmin har doim django.contrib.admin dan yuqorida turishi shart
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Uchinchi tomon kutubxonalari
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    "rangefilter",

    # Loyiha ilovalari
    "accounts",
    "catalog",
    "orders",
    "delivery",
    "promotions",
    "core",
]

# ============================================================
# MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# ============================================================
# TEMPLATES
# ============================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Agar context_processors faylingizda 'site_settings' bo'lsa shuni,
                # 'dashboard' bo'lsa pastdagini qoldiring:
                "core.context_processors.dashboard",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ============================================================
# MA'LUMOTLAR BAZASI
# ============================================================
# .env da USE_POSTGRES=True bo'lsa PostgreSQL, aks holda SQLite
if config("USE_POSTGRES", default=False, cast=bool):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME"),
            "USER": config("DB_USER"),
            "PASSWORD": config("DB_PASSWORD"),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Parol talablari (Standart to'liq xavfsizlik to'plami)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Hududiy sozlamalar
LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# Statik va Media fayllar
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================================
# DJANGO REST FRAMEWORK & XAVFSIZLIK (Throttling, Pagination, JWT)
# ============================================================
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    # Respublika miqyosidagi katta ma'lumotlar oqimi uchun sahifalash (Pagination)
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # DDOS va spam so'rovlardan himoya (Throttling)
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/minute",
        "user": "1000/minute",
    },
}

# SimpleJWT sozlamalari (Mobil va Frontend uchun)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# Swagger / OpenAPI sozlamalari
SPECTACULAR_SETTINGS = {
    "TITLE": "DUOO E-Commerce & B2B API",
    "DESCRIPTION": "DUOO platformasining buyurtmalar, katalog, yetkazib berish va do'konlar boshqaruvi API hujjatlari",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ============================================================
# KESH VA ASINXRON VAZIFALAR (Redis & Celery)
# ============================================================
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ============================================================
# CORS VA CSRF SOZLAMALARI
# ============================================================
CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL", default=DEBUG, cast=bool)

CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:3000,http://127.0.0.1:3000,https://duoo.uz,https://www.duoo.uz",
    cast=Csv(),
)

# ============================================================
# JAZZMIN — Admin boshqaruv paneli ko'rinishi
# ============================================================
JAZZMIN_SETTINGS = {
    "site_title": "DUOO",
    "site_header": "DUOO",
    "site_brand": "DUOO",
    "welcome_sign": "DUOO boshqaruv paneliga xush kelibsiz",
    "copyright": "DUOO",
    "search_model": ["orders.Order", "accounts.Shop"],

    # Yuqori menyu
    "topmenu_links": [
        {"name": "Boshqaruv paneli", "url": "admin:index"},
        {"name": "Buyurtmalar", "model": "orders.order"},
        {"name": "Do'konlar", "model": "accounts.shop"},
        {"name": "Jamlangan yuk xati", "url": "/admin/waybill/grouped/"},
        {"name": "Brend yuk xati", "url": "/admin/waybill/by-brand/"},
    ],

    # Chap menyu ikonkalari
    "icons": {
        "accounts.User": "fas fa-users",
        "accounts.Shop": "fas fa-store",
        "accounts.Region": "fas fa-map-marked-alt",
        "accounts.District": "fas fa-map-marker-alt",
        "catalog.Category": "fas fa-layer-group",
        "catalog.Brand": "fas fa-trademark",
        "catalog.Product": "fas fa-box",
        "orders.Order": "fas fa-receipt",
        "orders.Payment": "fas fa-money-bill-wave",
        "orders.Cart": "fas fa-shopping-cart",
        "delivery.DeliveryRoute": "fas fa-route",
        "delivery.DeliveryStop": "fas fa-truck",
        "promotions.Banner": "fas fa-image",
        "promotions.PromoScreen": "fas fa-bullhorn",
        "core.AppVersion": "fas fa-mobile-alt",
        "core.Feedback": "fas fa-comment-dots",
        "core.SiteConfig": "fas fa-cog",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # Menyu bo'limlarining mantiqiy tartibi
    "order_with_respect_to": [
        "orders", "accounts", "catalog", "delivery", "promotions", "core", "auth",
    ],

    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "body_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-success",
    "navbar": "navbar-success navbar-dark",
    "no_navbar_border": True,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_flat_style": True,
    "theme": "flatly",
    "button_classes": {
        "primary": "btn-success",
        "success": "btn-success",
    },
}
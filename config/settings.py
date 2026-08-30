"""
GoDostavka — B2B ulgurji savdo tizimi. Django sozlamalari.
"""
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-insecure-key")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*", cast=Csv())

INSTALLED_APPS = [
    "jazzmin",  # admin panel temasi (django.contrib.admin dan oldin turishi shart)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "rest_framework",
    "corsheaders",
    # local
    "accounts",
    "catalog",
    "orders",
    "delivery",
    "promotions",
    "core",
]

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
                "core.context_processors.dashboard",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Boshlanishi uchun SQLite. Respublika miqyosida PostgreSQL'ga o'tamiz.
# Baza: .env da USE_POSTGRES=True bo'lsa PostgreSQL, aks holda SQLite (dev)
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

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    # Pagination — bir so'rovda 20 tadan (respublika miqyosi uchun muhim).
    "DEFAULT_PAGINATION_CLASS":
        "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
}

CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL", default=True, cast=bool)


# ============================================================
# JAZZMIN — admin panel ko'rinishi (boshqaruv paneli)
# ============================================================
JAZZMIN_SETTINGS = {
    "site_title": "GoDostavka",
    "site_header": "GoDostavka",
    "site_brand": "GoDostavka",
    "welcome_sign": "GoDostavka boshqaruv paneliga xush kelibsiz",
    "copyright": "GoDostavka",
    "search_model": ["orders.Order", "accounts.Shop"],

    # Yuqori menyu
    "topmenu_links": [
        {"name": "Boshqaruv paneli", "url": "admin:index"},
        {"name": "Buyurtmalar", "model": "orders.order"},
        {"name": "Do'konlar", "model": "accounts.shop"},
        {"name": "Jamlangan yuk xati", "url": "/admin/waybill/grouped/"},
    ],

    # Chap menyu tartibi va ikonlari
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
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # Menyu bo'limlar tartibi (mantiqiy)
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
    "brand_colour": "navbar-success",   # sariq brend rangi
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


# HTTPS/domen uchun (production)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://duoo.uz,https://www.duoo.uz",
    cast=Csv(),
)
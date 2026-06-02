import os
from pathlib import Path
from datetime import timedelta
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])

DJANGO_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "cloudinary_storage",
    "django.contrib.staticfiles",
    "cloudinary",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "channels",
    "django_celery_beat",
    "django_celery_results",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.authentication",
    "apps.users",
    "apps.shops",
    "apps.products",
    "apps.cart",
    "apps.orders",
    "apps.payments",
    "apps.wallet",
    "apps.udhaar",
    "apps.emi",
    "apps.delivery",
    "apps.notifications",
    "apps.coupons",
    "apps.support",
    "apps.iot",
    "apps.gis",
    "apps.videos",
    "apps.whatsapp",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ─── Databases ────────────────────────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

MONGODB = {
    "HOST": env("MONGO_HOST", default="localhost"),
    "PORT": env.int("MONGO_PORT", default=27017),
    "DB_NAME": env("MONGO_DB_NAME"),
    "USER": env("MONGO_USER"),
    "PASSWORD": env("MONGO_PASSWORD"),
}

# ─── Cache & Channel Layer ────────────────────────────────────────────────────

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL")],
        },
    },
}

# ─── Auth ─────────────────────────────────────────────────────────────────────

AUTH_USER_MODEL = "users.User"

# ─── DRF ──────────────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("ACCESS_TOKEN_LIFETIME_MINUTES", default=60)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("REFRESH_TOKEN_LIFETIME_DAYS", default=7)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ─── Email ────────────────────────────────────────────────────────────────────

EMAIL_BACKEND     = env("EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST        = env("EMAIL_HOST",    default="smtp-relay.brevo.com")
EMAIL_PORT        = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS     = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER   = env("EMAIL_HOST_USER",     default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL",
    default="QabiFly <noreply@qalbconverfy.in>")

# ─── OTP ──────────────────────────────────────────────────────────────────────

EMAIL_OTP_EXPIRY_MINUTES = env.int("EMAIL_OTP_EXPIRY_MINUTES", default=10)
PHONE_OTP_EXPIRY_MINUTES = env.int("PHONE_OTP_EXPIRY_MINUTES", default=5)
OTP_LENGTH               = env.int("OTP_LENGTH", default=6)

# ─── API Docs ─────────────────────────────────────────────────────────────────

SPECTACULAR_SETTINGS = {
    "TITLE":       "QabiFly API",
    "DESCRIPTION": "Hyperlocal e-commerce — Reoti Block, Ballia UP",
    "VERSION":     "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ─── Celery ───────────────────────────────────────────────────────────────────

CELERY_BROKER_URL        = env("REDIS_URL")
CELERY_RESULT_BACKEND    = "django-db"
CELERY_ACCEPT_CONTENT    = ["json"]
CELERY_TASK_SERIALIZER   = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE          = "Asia/Kolkata"
CELERY_BEAT_SCHEDULER    = "django_celery_beat.schedulers:DatabaseScheduler"

# ─── Localisation ─────────────────────────────────────────────────────────────

LANGUAGE_CODE = "en-us"
TIME_ZONE     = "Asia/Kolkata"
USE_I18N      = True
USE_TZ        = True

# ─── Static ───────────────────────────────────────────────────────────────────

STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Cloudinary ───────────────────────────────────────────────────────────────

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME", default=""),
    "API_KEY":    env("CLOUDINARY_API_KEY",    default=""),
    "API_SECRET": env("CLOUDINARY_API_SECRET", default=""),
    "SECURE":     True,
}


# Default — override in dev/prod
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
MEDIA_URL = "/media/"

# ─── Platform Rules ───────────────────────────────────────────────────────────

PLATFORM_COMMISSION_PERCENT = env.int("PLATFORM_COMMISSION_PERCENT", default=5)
SHOPKEEPER_PERCENT          = env.int("SHOPKEEPER_PERCENT",           default=92)
DELIVERY_BOY_PERCENT        = env.int("DELIVERY_BOY_PERCENT",         default=3)
MAX_UDHAAR_LIMIT            = env.int("MAX_UDHAAR_LIMIT",             default=20000)
DELIVERY_RADIUS_KM          = 2

# ─── External Services ────────────────────────────────────────────────────────
# Firebase
FIREBASE_CREDENTIALS_PATH = env("FIREBASE_CREDENTIALS_PATH",default="/app/firebase-credentials.json")

FAST2SMS_API_KEY  = env("FAST2SMS_API_KEY",  default="")
RAZORPAY_KEY_ID   = env("RAZORPAY_KEY_ID",   default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET", default="")
GOOGLE_CLIENT_ID  = env("GOOGLE_CLIENT_ID",  default="")

# WhatsApp
WHATSAPP_PHONE_NUMBER_ID     = env("WHATSAPP_PHONE_NUMBER_ID",     default="")
WHATSAPP_BUSINESS_ACCOUNT_ID = env("WHATSAPP_BUSINESS_ACCOUNT_ID", default="")
WHATSAPP_ACCESS_TOKEN        = env("WHATSAPP_ACCESS_TOKEN",        default="")
WHATSAPP_VERIFY_TOKEN        = env("WHATSAPP_VERIFY_TOKEN",
    default="qabifly-webhook-secret-2024")
WHATSAPP_API_URL             = env("WHATSAPP_API_URL",
    default="https://graph.facebook.com/v19.0")

# ─── Logging ──────────────────────────────────────────────────────────────────

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style":  "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style":  "{",
        },
    },
    "handlers": {
        "file": {
            "level":     "INFO",
            "class":     "logging.FileHandler",
            "filename":  BASE_DIR / "logs/qabifly.log",
            "formatter": "verbose",
        },
        "console": {
            "class":     "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level":    "INFO",
    },
    "loggers": {
        "django": {
            "handlers":  ["console", "file"],
            "level":     "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers":  ["console", "file"],
            "level":     "INFO",
            "propagate": False,
        },
    },
}

# config/settings/base.py mein add karo:

JAZZMIN_SETTINGS = {
    "site_title":    "QabiFly Admin",
    "site_header":   "QabiFly",
    "site_brand":    "QabiFly",
    "welcome_sign":  "QabiFly Admin Panel — Reoti, Ballia",
    "copyright":     "ZEAIPC",
    "search_model":  ["users.User", "orders.Order", "shops.Shop"],
    "topmenu_links": [
        {"name": "Home",    "url": "admin:index"},
        {"name": "API Docs","url": "/api/docs/", "new_window": True},
    ],
    "icons": {
        "users.User":         "fas fa-users",
        "shops.Shop":         "fas fa-store",
        "orders.Order":       "fas fa-box",
        "wallet.Wallet":      "fas fa-wallet",
        "udhaar.UdhaarRecord":"fas fa-book",
    },
    "show_sidebar":       True,
    "navigation_expanded": True,
    "order_with_respect_to": [
        "users", "shops", "products",
        "orders", "payments", "wallet",
        "udhaar", "emi", "delivery",
    ],
}

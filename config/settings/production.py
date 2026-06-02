from .base import *
import os
import environ

DEBUG = False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS","qabifly.vps.qalbconverfy.in,localhost,127.0.0.1")

CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS","")

CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS","")

CORS_ALLOW_CREDENTIALS = True

# ─── Security ─────────────────────────────────────────────────────────────────

SECURE_BROWSER_XSS_FILTER      = True
SECURE_CONTENT_TYPE_NOSNIFF    = True
X_FRAME_OPTIONS                = "DENY"
SECURE_HSTS_SECONDS            = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT            = True
SESSION_COOKIE_SECURE          = True
CSRF_COOKIE_SECURE             = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ─── Storage — Cloudinary ─────────────────────────────────────────────────────

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
MEDIA_URL = "/media/"

# ─── Static ───────────────────────────────────────────────────────────────────

STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

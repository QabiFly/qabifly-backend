from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "qalbconverfy.in",
    "qabifly.vps.qalbconverfy.in",
    "www.qalbconverfy.in",
    "qabifly.edgeone.app",
]

CORS_ALLOWED_ORIGINS = [
    "https://qalbconverfy.in",
    "https://qabifly.vps.qalbconverfy.in",
    "https://qabifly.edgeone.app",
]

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

# ─── Storage — Cloudinary ─────────────────────────────────────────────────────

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
MEDIA_URL = "/media/"

# ─── Static ───────────────────────────────────────────────────────────────────

STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

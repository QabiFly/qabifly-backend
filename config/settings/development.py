from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS  = True
CORS_ALLOW_CREDENTIALS  = True

# ─── Storage — Local in dev ───────────────────────────────────────────────────
# Cloudinary use karna ho toh neeche wali 2 lines comment karo

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─── Email — Console in dev ───────────────────────────────────────────────────
# Real email test karna ho toh comment karo

# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ─── Relaxed passwords in dev ─────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = []

# ─── Dev-only logging ─────────────────────────────────────────────────────────

LOGGING["loggers"]["apps"]["level"] = "DEBUG"

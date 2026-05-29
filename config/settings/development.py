from .base import *

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True

# Override email to console in development — no SMTP server needed locally
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Local file storage in development
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# Relaxed password validation in dev
AUTH_PASSWORD_VALIDATORS = []
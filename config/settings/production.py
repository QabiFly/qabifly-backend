from .base import *
import environ

env = environ.Env()

DEBUG = False

ALLOWED_HOSTS = [
    "qalbconverfy.in",
    "qabifly.vps.qalbconverfy.in",
    "www.qalbconverfy.in",
]

CORS_ALLOWED_ORIGINS = [
    "https://qalbconverfy.in",
    "https://qabifly.vps.qalbconverfy.in",
]

SECURE_BROWSER_XSS_FILTER      = True
SECURE_CONTENT_TYPE_NOSNIFF    = True
X_FRAME_OPTIONS                = "DENY"
SECURE_HSTS_SECONDS            = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT            = True
SESSION_COOKIE_SECURE          = True
CSRF_COOKIE_SECURE             = True

EMAIL_BACKEND       = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST          = env("EMAIL_HOST",    default="smtp-relay.brevo.com")
EMAIL_PORT          = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS       = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER     = env("EMAIL_HOST_USER",     default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

if USE_S3:
    _bucket = AWS_STORAGE_BUCKET_NAME
    _region = AWS_S3_REGION_NAME
    AWS_S3_CUSTOM_DOMAIN   = f"{_bucket}.s3.{_region}.amazonaws.com"
    DEFAULT_FILE_STORAGE   = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE    = "storages.backends.s3boto3.S3StaticStorage"
    MEDIA_URL  = f"https://{_bucket}.s3.{_region}.amazonaws.com/media/"
    STATIC_URL = f"https://{_bucket}.s3.{_region}.amazonaws.com/static/"
else:
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_URL  = "/media/"
    STATIC_URL = "/static/"

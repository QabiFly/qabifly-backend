from .base import *
import environ

env = environ.Env()

DEBUG = False

ALLOWED_HOSTS = [
    "qalbconverfy.in",
    "qabifly.vps.qalbconverfy.in",
    "www.qalbconverfy.in",
    "http://localhost:7700",
    "http://127.0.0.1:7700",
]

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "https://qalbconverfy.in",
        "https://qabifly.vps.qalbconverfy.in",
        "http://localhost:7700",
        "http://127.0.0.1:7700",
    ]
)

# Security
SECURE_BROWSER_XSS_FILTER      = True
SECURE_CONTENT_TYPE_NOSNIFF    = True
X_FRAME_OPTIONS                = "DENY"
SECURE_HSTS_SECONDS            = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT            = True
SESSION_COOKIE_SECURE          = True
CSRF_COOKIE_SECURE             = True

# Email
EMAIL_BACKEND     = env("EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST        = env("EMAIL_HOST",     default="smtp-relay.brevo.com")
EMAIL_PORT        = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS     = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER   = env("EMAIL_HOST_USER",     default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

# ── S3 Storage ────────────────────────────────────────────────────────────────
if env.bool("USE_S3", default=False):

    # AWS Credentials
    AWS_ACCESS_KEY_ID       = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY   = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME      = env("AWS_S3_REGION_NAME", default="ap-south-1")

    # S3 Settings
    AWS_DEFAULT_ACL          = None
    AWS_S3_FILE_OVERWRITE    = False
    AWS_QUERYSTRING_AUTH     = False  # Public URLs chahiye

    # Custom domain nahi — direct S3 URL use karo
    AWS_S3_CUSTOM_DOMAIN = (
        f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
    )

    # Storage backends
    DEFAULT_FILE_STORAGE   = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE    = "storages.backends.s3boto3.S3StaticStorage"

    # Media aur Static alag folders mein
    MEDIAFILES_LOCATION = "media"
    STATICFILES_LOCATION = "static"

    MEDIA_URL  = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"

else:
    # Local storage
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_URL  = "/media/"
    STATIC_URL = "/static/"

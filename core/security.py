import re
import bleach
import logging
from functools import wraps
from django.http import JsonResponse

logger = logging.getLogger("apps")


def sanitize_text(text: str, max_length: int = 500) -> str:
    if not text:
        return ""
    clean = bleach.clean(str(text), tags=[], strip=True)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:max_length]


def sanitize_phone(phone: str) -> str:
    return re.sub(r'[^\d+]', '', str(phone))[:15]


def validate_file_upload(file, allowed_types=None, max_mb=5):
    """
    File upload validate karo.
    allowed_types: ['image/jpeg','image/png','application/pdf']
    """
    if allowed_types is None:
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']

    if file.content_type not in allowed_types:
        raise ValueError(
            f"File type '{file.content_type}' allowed nahi hai."
        )

    max_bytes = max_mb * 1024 * 1024
    if file.size > max_bytes:
        raise ValueError(
            f"File size {max_mb}MB se zyada nahi hona chahiye."
        )

    return True


def get_client_ip(request) -> str:
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')

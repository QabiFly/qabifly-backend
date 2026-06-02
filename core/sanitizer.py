import re
import bleach


def sanitize_text(text: str, max_length: int = 500) -> str:
    """XSS prevent karo, length limit karo."""
    if not text:
        return ""
    # HTML tags hatao
    clean = bleach.clean(str(text), tags=[], strip=True)
    # Extra whitespace hatao
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:max_length]


def sanitize_phone(phone: str) -> str:
    """Sirf digits aur + allow karo."""
    return re.sub(r'[^\d+]', '', phone)[:15]


def sanitize_order_note(text: str) -> str:
    return sanitize_text(text, max_length=200)

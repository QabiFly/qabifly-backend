import random
import string
from django.utils import timezone


def generate_order_number() -> str:
    """
    Format: QF-YYYYMMDD-XXXXX
    e.g.  : QF-20240615-A8K2P
    """
    date_part   = timezone.now().strftime("%Y%m%d")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"QF-{date_part}-{random_part}"


def generate_delivery_otp() -> str:
    return "".join(random.choices(string.digits, k=6))
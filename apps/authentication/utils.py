import logging
import httpx
from django.conf import settings
from django.utils import timezone
from .models import OTPRecord

logger = logging.getLogger("apps")


def get_or_create_otp(identifier: str, otp_type: str) -> OTPRecord:
    """
    Invalidate any previous unused OTPs for same identifier+type,
    then create a fresh one.
    """
    OTPRecord.objects.filter(
        identifier=identifier,
        otp_type=otp_type,
        is_used=False,
    ).update(is_used=True)

    record = OTPRecord.objects.create(
        identifier=identifier,
        otp_type=otp_type,
    )
    return record


def verify_otp(identifier: str, otp_code: str, otp_type: str) -> tuple[bool, str]:
    """
    Returns (success: bool, message: str)
    """
    try:
        record = OTPRecord.objects.filter(
            identifier=identifier,
            otp_type=otp_type,
            is_used=False,
        ).latest("created_at")
    except OTPRecord.DoesNotExist:
        return False, "No OTP found. Please request a new one."

    if record.is_expired:
        return False, "OTP has expired. Please request a new one."

    if record.attempts >= 5:
        return False, "Too many wrong attempts. Please request a new OTP."

    if record.otp_code != otp_code:
        record.attempts += 1
        record.save(update_fields=["attempts"])
        remaining = 5 - record.attempts
        return False, f"Incorrect OTP. {remaining} attempts remaining."

    record.is_used = True
    record.save(update_fields=["is_used"])
    return True, "OTP verified successfully."


def send_phone_otp(phone: str, otp_code: str) -> bool:
    """Send OTP via Fast2SMS — only for optional phone verification."""
    api_key = settings.FAST2SMS_API_KEY
    if not api_key:
        logger.warning("FAST2SMS_API_KEY not set — phone OTP not sent.")
        return False

    try:
        response = httpx.post(
            "https://www.fast2sms.com/dev/bulkV2",
            headers={"authorization": api_key},
            json={
                "route": "otp",
                "variables_values": otp_code,
                "flash": 0,
                "numbers": phone.replace("+91", ""),
            },
            timeout=10,
        )
        data = response.json()
        if data.get("return"):
            logger.info(f"Phone OTP sent to {phone}")
            return True
        else:
            logger.error(f"Fast2SMS error: {data}")
            return False
    except Exception as e:
        logger.error(f"Fast2SMS request failed: {e}")
        return False
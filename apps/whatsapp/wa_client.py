import httpx
import logging
from django.conf import settings

logger = logging.getLogger("apps")

BASE_URL = settings.WHATSAPP_API_URL
PHONE_ID = settings.WHATSAPP_PHONE_NUMBER_ID
TOKEN    = settings.WHATSAPP_ACCESS_TOKEN


def _headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type":  "application/json",
    }


def send_text(to: str, message: str) -> bool:
    """
    Simple text message bhejo.
    `to` = phone number with country code, no '+' (e.g. 916387403745)
    """
    url     = f"{BASE_URL}/{PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type":    "individual",
        "to":                to,
        "type":              "text",
        "text":              {"body": message},
    }
    try:
        res = httpx.post(url, json=payload, headers=_headers(), timeout=10)
        if res.status_code == 200:
            logger.info(f"WhatsApp message sent to {to}")
            return True
        else:
            logger.error(f"WhatsApp API error: {res.text}")
            return False
    except Exception as e:
        logger.error(f"WhatsApp send failed: {e}")
        return False


def send_order_alert_to_shopkeeper(
    shopkeeper_phone: str,
    order_number: str,
    buyer_name: str,
    total: float,
    payment_method: str,
    items_summary: str,
) -> bool:
    """
    Shopkeeper ko naye order ka alert bhejo with Accept/Reject buttons.
    """
    message = (
        f"🛒 *Naya Order Aaya!*\n\n"
        f"Order: *#{order_number}*\n"
        f"Customer: {buyer_name}\n"
        f"Amount: *₹{total}*\n"
        f"Payment: {payment_method}\n\n"
        f"📦 Items:\n{items_summary}\n\n"
        f"Reply karo:\n"
        f"*1* → ✅ Accept\n"
        f"*2* → ❌ Reject\n"
        f"*3* → 📋 Order detail dekho"
    )
    return send_text(shopkeeper_phone, message)


def send_order_status_to_buyer(
    buyer_phone: str,
    order_number: str,
    status: str,
    message_extra: str = "",
) -> bool:
    """Buyer ko order status update bhejo."""
    status_emojis = {
        "CONFIRMED": "✅ Confirm ho gaya",
        "PREPARING": "👨‍🍳 Taiyaar ho raha hai",
        "READY":     "📦 Ready hai pickup ke liye",
        "PICKED":    "🚴 Raste mein hai",
        "DELIVERED": "🎉 Deliver ho gaya!",
        "CANCELLED": "❌ Cancel ho gaya",
    }
    status_text = status_emojis.get(status, status)
    message = (
        f"📱 *QabiFly Order Update*\n\n"
        f"Order #{order_number}\n"
        f"Status: *{status_text}*"
    )
    if message_extra:
        message += f"\n\n{message_extra}"
    return send_text(buyer_phone, message)


def send_otp(phone: str, otp: str, name: str = "User") -> bool:
    """WhatsApp pe OTP bhejo."""
    message = (
        f"🔐 *QabiFly Login OTP*\n\n"
        f"Namaste {name}!\n\n"
        f"Aapka OTP hai: *{otp}*\n\n"
        f"Yeh OTP 10 minute mein expire ho jayega.\n"
        f"Kisi ke saath share mat karein.\n\n"
        f"_QabiFly - Apna Gaon, Apna Bazaar_"
    )
    return send_text(phone, message)


def send_udhaar_reminder(
    phone: str,
    buyer_name: str,
    shop_name: str,
    amount: float,
    due_date: str,
) -> bool:
    """Udhaar due date reminder."""
    message = (
        f"📒 *Digital Khata Reminder*\n\n"
        f"Namaste {buyer_name}!\n\n"
        f"*{shop_name}* ka udhaar:\n"
        f"Baki: *₹{amount}*\n"
        f"Due Date: *{due_date}*\n\n"
        f"Abhi pay karne ke liye reply karein:\n"
        f"*PAY* → Payment options dekho\n\n"
        f"_QabiFly Digital Khata_"
    )
    return send_text(phone, message)

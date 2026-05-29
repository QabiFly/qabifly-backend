from urllib.parse import urlencode
from django.conf import settings

MERCHANT_UPI_ID = "6387403745@fam"
MERCHANT_NAME   = "QabiFly"


def generate_upi_deep_link(amount: float, order_number: str, note: str = "") -> dict:
    """
    Generate UPI deep link for payment.
    Works with GPay, PhonePe, Paytm, BHIM — all UPI apps.

    Returns:
        {
            "upi_link": "upi://pay?...",
            "intent_link": "intent://pay?...#Intent;...",  # Android fallback
            "amount": 299.00,
            "upi_id": "6387403745@fam"
        }
    """
    params = {
        "pa": MERCHANT_UPI_ID,        # payee address (UPI ID)
        "pn": MERCHANT_NAME,          # payee name
        "am": f"{float(amount):.2f}", # amount
        "cu": "INR",                  # currency
        "tn": note or f"QabiFly Order {order_number}",  # transaction note
        "tr": order_number,           # transaction reference
    }

    query_string = urlencode(params)
    upi_link     = f"upi://pay?{query_string}"

    # Android intent link (fallback if upi:// scheme not handled)
    intent_link = (
        f"intent://pay?{query_string}"
        f"#Intent;scheme=upi;package=com.google.android.apps.nbu.paisa.user;end"
    )

    return {
        "upi_link":    upi_link,
        "intent_link": intent_link,
        "gpay_link":   f"tez://upi/pay?{query_string}",
        "phonepe_link": f"phonepe://pay?{query_string}",
        "paytm_link":  f"paytmmp://pay?{query_string}",
        "amount":      float(amount),
        "upi_id":      MERCHANT_UPI_ID,
        "order_number": order_number,
        "instruction": (
            "1. Open any UPI app (GPay, PhonePe, Paytm, BHIM)\n"
            "2. Amount and UPI ID are pre-filled\n"
            "3. Complete payment\n"
            "4. Come back and enter your UTR/Transaction ID"
        ),
    }
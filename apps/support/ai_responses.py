"""
Rule-based AI auto-responses — no external API needed.
Common questions ke liye instant answers.
"""

RESPONSES = {
    "order": {
        "keywords": ["order", "cancel", "track", "status", "kahan hai", "order kahan"],
        "response": (
            "Aapka order track karne ke liye app mein 'My Orders' section mein jayein. "
            "Order cancel karne ke liye PENDING ya CONFIRMED status mein hi cancel button dikhega. "
            "Agar delivery mein zyada time lag raha hai, please 30 minute wait karein. "
            "Problem persist kare toh hum agent se connect karenge."
        ),
    },
    "payment": {
        "keywords": ["payment", "pay", "upi", "paise", "refund", "wallet"],
        "response": (
            "UPI payment ke liye: order place karein → UPI link pe click karein → "
            "apna UPI app khulega → pay karein → UTR number submit karein. "
            "Wallet refund 24 ghante mein process hota hai. "
            "COD mein delivery pe cash dena hota hai."
        ),
    },
    "delivery": {
        "keywords": ["delivery", "deliver", "deliver nahi", "late", "boy", "agent"],
        "response": (
            "Delivery boy ka real-time location app mein track kar sakte hain. "
            "Delivery 2km radius mein hoti hai. "
            "Agar delivery boy contact nahi kar raha — delivery OTP share na karein "
            "jab tak saman haath mein na aa jaye."
        ),
    },
    "udhaar": {
        "keywords": ["udhaar", "credit", "khata", "due", "sunday"],
        "response": (
            "Udhaar limit ₹20,000 hai. "
            "Due date pe payment na ho toh Sunday collection hoti hai. "
            "Apna udhaar dekho: App → Udhaar section. "
            "Payment karne ke liye: Wallet, UPI, ya cash se pay kar sakte hain."
        ),
    },
    "account": {
        "keywords": ["login", "password", "account", "otp", "email", "register"],
        "response": (
            "OTP nahi aaya? Spam folder check karein. "
            "Password bhool gaye? Login page pe 'Forgot Password' use karein. "
            "Account band hai? Admin se contact karein. "
            "Phone number update karne ke liye: Profile → Edit → Phone."
        ),
    },
}


def get_auto_response(subject: str, message: str) -> str | None:
    """
    Returns an auto-response string if keywords match,
    or None if no match (escalate to human agent).
    """
    text = (subject + " " + message).lower()

    for category, info in RESPONSES.items():
        for keyword in info["keywords"]:
            if keyword in text:
                return info["response"]

    return None
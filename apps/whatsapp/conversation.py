import random
import string
import logging
from django.utils import timezone
from django.conf import settings
from apps.users.models import User
from apps.authentication.models import OTPRecord
from .models import WhatsAppSession, WhatsAppMessage
from .wa_client import send_text, send_otp

logger = logging.getLogger("apps")


def generate_otp():
    return "".join(random.choices(string.digits, k=6))


def get_or_create_session(phone: str) -> WhatsAppSession:
    session, _ = WhatsAppSession.objects.get_or_create(phone=phone)
    return session


def log_message(session, direction, content, wa_msg_id=""):
    WhatsAppMessage.objects.create(
        session    = session,
        direction  = direction,
        content    = content,
        wa_msg_id  = wa_msg_id,
    )


def handle_incoming(phone: str, message: str, wa_msg_id: str = ""):
    """
    Main conversation handler.
    Har incoming message yahan aata hai.
    State machine se handle hota hai.
    """
    session = get_or_create_session(phone)
    log_message(session, "INBOUND", message, wa_msg_id)

    msg = message.strip().lower()

    # Global commands — kisi bhi state mein kaam karte hain
    if msg in ("hi", "hello", "helo", "salaam", "start", "menu"):
        return _handle_start(session, phone)

    if msg in ("help", "madad"):
        return _handle_help(session, phone)

    if msg in ("cancel", "band karo", "exit"):
        return _reset_session(session, phone)

    # State-based handling
    handlers = {
        "IDLE":          _handle_idle,
        "AWAITING_NAME": _handle_name,
        "AWAITING_OTP":  _handle_otp,
        "AWAITING_EMAIL": _handle_email,
        "AUTHENTICATED": _handle_authenticated_menu,
        "ORDER_MENU":    _handle_order_menu,
    }

    handler = handlers.get(session.state, _handle_idle)
    handler(session, phone, msg)


def _handle_start(session, phone):
    """New user ya returning user greeting."""
    if session.user:
        # Returning user
        user = session.user
        session.state = "AUTHENTICATED"
        session.save()
        _reply(session, phone,
            f"👋 Wapas aaye {user.full_name}!\n\n"
            f"Kya karna chahte hain?\n\n"
            f"*1* → 📦 Mere Orders\n"
            f"*2* → 💰 Wallet Balance\n"
            f"*3* → 📒 Digital Khata\n"
            f"*4* → 🛒 Shopping karo\n"
            f"*5* → 🚪 Logout"
        )
    else:
        # New user
        session.state = "AWAITING_NAME"
        session.save()
        _reply(session, phone,
            f"🙏 *QabiFly mein Aapka Swagat Hai!*\n"
            f"_Apna Gaon, Apna Bazaar_\n\n"
            f"Reoti Block ka apna platform!\n\n"
            f"Pehle apna *poora naam* likhein:"
        )


def _handle_idle(session, phone, msg):
    _handle_start(session, phone)


def _handle_name(session, phone, msg):
    """User ne naam diya — OTP bhejo."""
    if len(msg) < 2:
        _reply(session, phone, "❌ Sahi naam likhein (kam se kam 2 akshar):")
        return

    name = msg.title()  # Capitalize
    session.temp_data = {"name": name}
    session.state = "AWAITING_OTP"
    session.save()

    # OTP generate karo
    otp = generate_otp()
    session.temp_data["otp"] = otp
    session.temp_data["otp_time"] = timezone.now().isoformat()
    session.save()

    # WhatsApp pe OTP bhejo
    send_otp(phone, otp, name)

    _reply(session, phone,
        f"✅ Shukriya, *{name}*!\n\n"
        f"Aapke WhatsApp number pe OTP bheja gaya hai.\n"
        f"OTP daalen (6 digit):"
    )


def _handle_otp(session, phone, msg):
    """OTP verify karo — account banao ya login karo."""
    stored_otp  = session.temp_data.get("otp")
    stored_name = session.temp_data.get("name", "User")

    if not stored_otp:
        session.state = "IDLE"
        session.save()
        _reply(session, phone, "❌ Session expire ho gaya. Dobara 'Hi' likho.")
        return

    if msg != stored_otp:
        _reply(session, phone, "❌ Galat OTP. Dobara daalen:")
        return

    # OTP sahi hai — user dhundo ya banao
    phone_formatted = f"+{phone}"

    user = User.objects.filter(phone=phone_formatted).first()

    if not user:
        # Naya user — email optional rahega
        user = User.objects.create_user(
            email       = f"{phone}@whatsapp.qabifly.in",
            password    = User.objects.make_random_password(),
            full_name   = stored_name,
            phone       = phone_formatted,
            role        = "BUYER",
            is_verified = True,
            is_phone_verified = True,
        )
        is_new = True
    else:
        user.full_name = stored_name
        user.is_verified = True
        user.save(update_fields=["full_name", "is_verified"])
        is_new = False

    # Session update karo
    session.user  = user
    session.state = "AUTHENTICATED"
    session.temp_data = {}
    session.save()

    welcome_msg = (
        f"🎉 *Account ban gaya!*\n" if is_new else
        f"✅ *Login ho gaye!*\n"
    )

    _reply(session, phone,
        f"{welcome_msg}\n"
        f"Namaste *{user.full_name}*! 👋\n\n"
        f"Aap QabiFly ke member hain.\n\n"
        f"Kya karna chahte hain?\n\n"
        f"*1* → 📦 Mere Orders\n"
        f"*2* → 💰 Wallet Balance\n"
        f"*3* → 📒 Digital Khata\n"
        f"*4* → 🛒 Shopping karo\n"
        f"*5* → 📞 Support"
    )


def _handle_email(session, phone, msg):
    """Optional email update."""
    import re
    if not re.match(r"[^@]+@[^@]+\.[^@]+", msg):
        _reply(session, phone, "❌ Sahi email daalen (e.g. arman@gmail.com):")
        return

    user = session.user
    if user:
        user.email = msg
        user.save(update_fields=["email"])

    session.state = "AUTHENTICATED"
    session.save()
    _reply(session, phone,
        f"✅ Email save ho gaya!\n\n"
        f"Ab aap QabiFly app mein bhi is email se login kar sakte hain.\n\n"
        f"Menu ke liye 'menu' likhein."
    )


def _handle_authenticated_menu(session, phone, msg):
    """Logged-in user ke options."""
    user = session.user

    if msg == "1":
        # Mere orders
        from apps.orders.models import Order
        orders = Order.objects.filter(
            buyer=user
        ).order_by("-created_at")[:5]

        if not orders:
            _reply(session, phone,
                "📦 *Mere Orders*\n\n"
                "Abhi koi order nahi hai.\n"
                "Shopping ke liye app kholo: qabifly.vps.qalbconverfy.in"
            )
        else:
            order_text = "📦 *Mere Orders (Last 5)*\n\n"
            for o in orders:
                order_text += (
                    f"#{o.order_number}\n"
                    f"₹{o.total_amount} | {o.status}\n"
                    f"---\n"
                )
            _reply(session, phone, order_text)

    elif msg == "2":
        # Wallet balance
        from apps.wallet.models import Wallet
        wallet, _ = Wallet.objects.get_or_create(user=user)
        _reply(session, phone,
            f"💰 *Mera Wallet*\n\n"
            f"Balance: *₹{wallet.balance}*\n"
            f"Total Kamaya: ₹{wallet.total_earned}\n"
            f"Total Kharch: ₹{wallet.total_spent}\n\n"
            f"Paise add karne ke liye app use karein."
        )

    elif msg == "3":
        # Udhaar
        from apps.udhaar.models import UdhaarRecord
        records = UdhaarRecord.objects.filter(
            buyer=user, is_settled=False
        )
        if not records:
            _reply(session, phone,
                "📒 *Digital Khata*\n\n"
                "Aapka koi udhaar nahi hai. 👍"
            )
        else:
            total = sum(r.amount_remaining for r in records)
            udhaar_text = f"📒 *Digital Khata*\n\nKul Baki: *₹{total}*\n\n"
            for r in records:
                udhaar_text += (
                    f"🏪 {r.shop.name}\n"
                    f"Baki: ₹{r.amount_remaining}\n"
                    f"Due: {r.due_date}\n---\n"
                )
            _reply(session, phone, udhaar_text)

    elif msg == "4":
        _reply(session, phone,
            "🛒 *Shopping*\n\n"
            "Reoti ke shops browse karne ke liye:\n"
            f"qabifly.vps.qalbconverfy.in\n\n"
            "Ya apna QabiFly app kholo."
        )

    elif msg == "5":
        _reply(session, phone,
            "📞 *Support*\n\n"
            "Koi problem hai?\n"
            "Humse baat karein:\n"
            "Email: support@qalbconverfy.in\n\n"
            "Ya ticket banao app mein."
        )

    else:
        _reply(session, phone,
            "Menu ke liye yeh options hain:\n\n"
            "*1* → 📦 Mere Orders\n"
            "*2* → 💰 Wallet Balance\n"
            "*3* → 📒 Digital Khata\n"
            "*4* → 🛒 Shopping karo\n"
            "*5* → 📞 Support"
        )


def _handle_order_menu(session, phone, msg):
    """Shopkeeper order accept/reject."""
    order_number = session.temp_data.get("pending_order")
    if not order_number:
        session.state = "AUTHENTICATED"
        session.save()
        return _handle_start(session, phone)

    from apps.orders.models import Order, OrderStatusLog
    try:
        order = Order.objects.get(order_number=order_number)
    except Order.DoesNotExist:
        _reply(session, phone, "❌ Order nahi mila.")
        session.state = "AUTHENTICATED"
        session.save()
        return

    if msg == "1":
        # Accept
        order.status      = Order.Status.CONFIRMED
        order.confirmed_at = timezone.now()
        order.save(update_fields=["status", "confirmed_at"])

        OrderStatusLog.objects.create(
            order       = order,
            from_status = "PENDING",
            to_status   = "CONFIRMED",
            note        = "Confirmed via WhatsApp",
        )

        # Buyer ko notify karo
        buyer = order.buyer
        if hasattr(buyer, "whatsapp_session"):
            from .wa_client import send_order_status_to_buyer
            send_order_status_to_buyer(
                buyer_phone    = buyer.whatsapp_session.phone,
                order_number   = order_number,
                status         = "CONFIRMED",
                message_extra  = f"Delivery jaldi hogi! 🚴",
            )

        _reply(session, phone,
            f"✅ Order #{order_number} *Accept* kar liya!\n\n"
            f"Customer ko notify kar diya gaya hai.\n"
            f"Order taiyaar hone pe '2' reply karein."
        )

        session.temp_data["pending_order"] = None
        session.state = "AUTHENTICATED"
        session.save()

    elif msg == "2":
        # Reject
        order.status = Order.Status.CANCELLED
        order.cancellation_reason = "Shopkeeper ne reject kiya WhatsApp se"
        order.cancelled_at = timezone.now()
        order.save()

        # Buyer notify
        buyer = order.buyer
        if hasattr(buyer, "whatsapp_session"):
            from .wa_client import send_order_status_to_buyer
            send_order_status_to_buyer(
                buyer_phone   = buyer.whatsapp_session.phone,
                order_number  = order_number,
                status        = "CANCELLED",
                message_extra = "Shop ne order accept nahi kiya. Kripya dobara try karein.",
            )

        _reply(session, phone, f"❌ Order #{order_number} reject kar diya.")
        session.temp_data["pending_order"] = None
        session.state = "AUTHENTICATED"
        session.save()

    elif msg == "3":
        # Order detail
        items_text = "\n".join(
            f"• {i.product_name} x{i.quantity} = ₹{i.line_total}"
            for i in order.items.all()
        )
        _reply(session, phone,
            f"📋 *Order #{order_number}*\n\n"
            f"Customer: {order.buyer.full_name}\n"
            f"Address: {order.delivery_address}\n"
            f"Payment: {order.payment_method}\n"
            f"Total: ₹{order.total_amount}\n\n"
            f"Items:\n{items_text}\n\n"
            f"*1* → Accept  *2* → Reject"
        )

    else:
        _reply(session, phone,
            "Reply karein:\n"
            "*1* → ✅ Accept\n"
            "*2* → ❌ Reject\n"
            "*3* → 📋 Detail"
        )


def _reset_session(session, phone):
    session.state     = "IDLE"
    session.temp_data = {}
    session.save()
    _reply(session, phone,
        "👋 Session reset ho gaya.\n"
        "Dobara shuru karne ke liye 'Hi' likhein."
    )


def _reply(session, phone, message):
    """Message bhejo aur log karo."""
    from .wa_client import send_text
    send_text(phone, message)
    log_message(session, "OUTBOUND", message)

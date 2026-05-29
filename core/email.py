import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger("apps")


def send_otp_email(to_email: str, otp: str, user_name: str = "User") -> bool:
    """
    Send an OTP verification email from noreply@qalbconverfy.in.
    Returns True on success, False on failure.
    """
    subject = "Your QabiFly Verification Code"
    text_body = (
        f"Hello {user_name},\n\n"
        f"Your QabiFly verification code is: {otp}\n\n"
        f"This code expires in {settings.EMAIL_OTP_EXPIRY_MINUTES} minutes.\n"
        f"Do not share this code with anyone.\n\n"
        f"— QabiFly Team\n"
        f"qalbconverfy.in"
    )
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:24px;border:1px solid #e5e7eb;border-radius:8px;">
      <h2 style="color:#1d4ed8;margin-bottom:8px;">QabiFly</h2>
      <p style="color:#374151;">Hello <strong>{user_name}</strong>,</p>
      <p style="color:#374151;">Your verification code is:</p>
      <div style="font-size:36px;font-weight:bold;letter-spacing:8px;color:#1d4ed8;
                  background:#eff6ff;padding:16px;border-radius:6px;text-align:center;
                  margin:16px 0;">{otp}</div>
      <p style="color:#6b7280;font-size:13px;">
        This code expires in <strong>{settings.EMAIL_OTP_EXPIRY_MINUTES} minutes</strong>.
        Do not share it with anyone.
      </p>
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;">
      <p style="color:#9ca3af;font-size:12px;">QabiFly · qalbconverfy.in · Reoti, Ballia</p>
    </div>
    """
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"OTP email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {e}")
        return False


def send_order_confirmation_email(to_email: str, order_id: str, total: str) -> bool:
    """Send order confirmation email after successful order placement."""
    subject = f"Order Confirmed — #{order_id}"
    text_body = (
        f"Your order #{order_id} has been confirmed.\n"
        f"Total: ₹{total}\n\n"
        f"Track your order on the QabiFly app.\n"
        f"— QabiFly Team"
    )
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        logger.error(f"Order confirmation email failed for {to_email}: {e}")
        return False
import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger("apps")


def send_otp_email(to_email: str, otp: str, user_name: str = "User") -> bool:
    """
    OTP email bhejo — Brevo SMTP se.
    Returns True on success, False on failure.
    """
    subject = "QabiFly — Aapka Verification Code"

    text_body = (
        f"Namaste {user_name},\n\n"
        f"Aapka QabiFly OTP hai: {otp}\n\n"
        f"Yeh code {settings.EMAIL_OTP_EXPIRY_MINUTES} minute mein expire ho jayega.\n"
        f"Kisi ke saath share mat karein.\n\n"
        f"— QabiFly Team\n"
        f"qalbconverfy.in"
    )

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
</head>
<body style="margin:0;padding:0;background:#f0f4ff;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 20px;">
        <table width="480" cellpadding="0" cellspacing="0"
               style="background:#fff;border-radius:16px;overflow:hidden;
                      box-shadow:0 4px 20px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#4B7BF5,#B044E8);
                       padding:28px 32px;text-align:center;">
              <div style="font-size:28px;margin-bottom:6px;">🛒</div>
              <div style="color:#fff;font-size:22px;font-weight:800;">
                QabiFly
              </div>
              <div style="color:rgba(255,255,255,0.75);font-size:12px;margin-top:4px;">
                Aapki Zarurat Hamari Zimmedari
              </div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              <p style="color:#374151;font-size:15px;margin:0 0 8px;">
                Namaste <strong>{user_name}</strong>,
              </p>
              <p style="color:#6b7280;font-size:14px;margin:0 0 24px;">
                Aapka verification code:
              </p>

              <!-- OTP Box -->
              <div style="background:#f0f4ff;border:2px solid #e0e7ff;
                          border-radius:12px;padding:20px;
                          text-align:center;margin-bottom:24px;">
                <div style="font-size:42px;font-weight:800;
                            letter-spacing:12px;color:#4B7BF5;
                            font-family:monospace;">
                  {otp}
                </div>
              </div>

              <p style="color:#6b7280;font-size:13px;margin:0 0 4px;">
                ⏰ Yeh code
                <strong>{settings.EMAIL_OTP_EXPIRY_MINUTES} minute</strong>
                mein expire hoga.
              </p>
              <p style="color:#6b7280;font-size:13px;margin:0;">
                🔒 Kisi ke saath share mat karein.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f9fafb;padding:16px 32px;
                       text-align:center;border-top:1px solid #f3f4f6;">
              <p style="color:#9ca3af;font-size:11px;margin:0;">
                QabiFly · qalbconverfy.in · Reoti, Ballia, UP
              </p>
              <p style="color:#9ca3af;font-size:11px;margin:4px 0 0;">
                Agar aapne yeh request nahi ki toh ignore karein.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    try:
        msg = EmailMultiAlternatives(
            subject      = subject,
            body         = text_body,
            from_email   = settings.DEFAULT_FROM_EMAIL,
            to           = [to_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"OTP email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"OTP email FAILED to {to_email}: {e}")
        return False


def send_order_confirmation_email(
    to_email: str,
    order_number: str,
    total: str,
    buyer_name: str = "Customer",
) -> bool:
    """Order confirmation email."""
    subject = f"QabiFly — Order #{order_number} Confirm Ho Gaya!"

    text_body = (
        f"Namaste {buyer_name},\n\n"
        f"Aapka order #{order_number} confirm ho gaya!\n"
        f"Total: Rs.{total}\n\n"
        f"App mein track karein.\n"
        f"— QabiFly Team"
    )

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f0f4ff;padding:40px 20px;">
  <div style="max-width:480px;margin:auto;background:#fff;
              border-radius:16px;overflow:hidden;
              box-shadow:0 4px 20px rgba(0,0,0,0.08);">
    <div style="background:linear-gradient(135deg,#4B7BF5,#B044E8);
                padding:24px;text-align:center;">
      <div style="color:#fff;font-size:20px;font-weight:800;">
        ✅ Order Confirm!
      </div>
    </div>
    <div style="padding:28px;">
      <p style="color:#374151;">Namaste <strong>{buyer_name}</strong>,</p>
      <p style="color:#6b7280;">Aapka order successfully place ho gaya!</p>
      <div style="background:#f0fdf4;border:1px solid #bbf7d0;
                  border-radius:10px;padding:16px;margin:16px 0;">
        <div style="font-size:13px;color:#166534;">
          Order Number: <strong>#{order_number}</strong>
        </div>
        <div style="font-size:20px;font-weight:800;color:#166534;margin-top:4px;">
          Total: Rs.{total}
        </div>
      </div>
      <p style="color:#6b7280;font-size:13px;">
        App mein real-time track karein.
      </p>
    </div>
    <div style="background:#f9fafb;padding:14px;text-align:center;">
      <p style="color:#9ca3af;font-size:11px;margin:0;">
        QabiFly · qalbconverfy.in
      </p>
    </div>
  </div>
</body>
</html>
"""

    try:
        msg = EmailMultiAlternatives(
            subject    = subject,
            body       = text_body,
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [to_email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Order confirmation email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Order confirmation email FAILED: {e}")
        return False

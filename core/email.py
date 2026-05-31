import logging
import base64
import os
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger("apps")


def _get_logo_base64() -> str:
    """Logo ko base64 mein convert karo."""
    logo_path = os.path.join(settings.BASE_DIR, "static", "logo.png")
    try:
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


def _logo_img_tag() -> str:
    """Logo img tag banao — base64 embedded."""
    b64 = _get_logo_base64()
    if b64:
        return f'<img src="data:image/png;base64,{b64}" alt="QabiFly" style="height:48px;width:auto;" />'
    else:
        return '<span style="font-size:28px;">🛒</span>'


def send_otp_email(to_email: str, otp: str, user_name: str = "User") -> bool:
    """OTP verification email — Brevo SMTP se."""

    subject = "QabiFly — Aapka Verification Code"

    text_body = (
        f"Namaste {user_name},\n\n"
        f"Aapka QabiFly OTP hai: {otp}\n\n"
        f"Yeh code {settings.EMAIL_OTP_EXPIRY_MINUTES} minute mein expire hoga.\n"
        f"Kisi ke saath share mat karein.\n\n"
        f"— QabiFly Team\n"
        f"Aapki Zarurat Hamari Zimmedari\n"
        f"qalbconverfy.in"
    )

    logo_tag = _logo_img_tag()

    html_body = f"""<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>QabiFly OTP</title>
</head>
<body style="margin:0;padding:0;background:#EEF2FF;font-family:'Segoe UI',Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
    <tr>
      <td align="center" style="padding:40px 16px;">

        <!-- Card -->
        <table width="520" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:20px;
                      overflow:hidden;
                      box-shadow:0 8px 32px rgba(75,123,245,0.12);">

          <!-- ── Header ── -->
          <tr>
            <td style="background:linear-gradient(135deg,#4B7BF5 0%,#9333EA 100%);
                       padding:32px 40px;text-align:center;">

              <!-- Logo -->
              <div style="margin-bottom:12px;">
                {logo_tag}
              </div>

              <!-- App Name -->
              <div style="color:#ffffff;font-size:26px;font-weight:800;
                          letter-spacing:-0.5px;line-height:1;">
                QabiFly
              </div>
              <div style="color:rgba(255,255,255,0.75);font-size:12px;
                          margin-top:5px;letter-spacing:0.5px;">
                AAPKI ZARURAT HAMARI ZIMMEDARI
              </div>
            </td>
          </tr>

          <!-- ── Greeting ── -->
          <tr>
            <td style="padding:32px 40px 0;">
              <p style="margin:0;font-size:16px;color:#374151;">
                Namaste <strong style="color:#4B7BF5;">{user_name}</strong> 👋
              </p>
              <p style="margin:8px 0 0;font-size:14px;color:#6B7280;line-height:1.6;">
                Aapne QabiFly mein login karne ki koshish ki hai.
                Neeche diya gaya code use karein:
              </p>
            </td>
          </tr>

          <!-- ── OTP Box ── -->
          <tr>
            <td style="padding:24px 40px;">
              <div style="background:linear-gradient(135deg,#EEF2FF,#F5F3FF);
                          border:2px solid #C7D2FE;
                          border-radius:16px;
                          padding:28px 20px;
                          text-align:center;">

                <div style="font-size:11px;font-weight:700;
                            color:#6366F1;letter-spacing:2px;
                            text-transform:uppercase;margin-bottom:12px;">
                  Verification Code
                </div>

                <!-- OTP digits -->
                <div style="display:inline-block;">
                  {''.join([
                      f'<span style="display:inline-block;width:44px;height:56px;'
                      f'background:#4B7BF5;color:#ffffff;'
                      f'font-size:28px;font-weight:800;'
                      f'border-radius:10px;text-align:center;'
                      f'line-height:56px;margin:0 4px;'
                      f'font-family:monospace;">{digit}</span>'
                      for digit in str(otp)
                  ])}
                </div>

                <!-- Timer -->
                <div style="margin-top:16px;font-size:13px;color:#6B7280;">
                  ⏰ {settings.EMAIL_OTP_EXPIRY_MINUTES} minute mein expire hoga
                </div>
              </div>
            </td>
          </tr>

          <!-- ── Warning ── -->
          <tr>
            <td style="padding:0 40px 24px;">
              <div style="background:#FEF3C7;border:1px solid #FDE68A;
                          border-radius:10px;padding:12px 16px;
                          display:flex;align-items:center;">
                <span style="font-size:16px;margin-right:8px;">⚠️</span>
                <span style="font-size:12px;color:#92400E;line-height:1.5;">
                  <strong>Dhyan dein:</strong> Yeh OTP sirf aapke liye hai.
                  Kisi ke saath — chahe woh QabiFly staff ho — share mat karein.
                </span>
              </div>
            </td>
          </tr>

          <!-- ── Steps ── -->
          <tr>
            <td style="padding:0 40px 28px;">
              <p style="font-size:13px;color:#374151;font-weight:600;margin:0 0 10px;">
                Kaise use karein:
              </p>
              <table cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td style="width:28px;height:28px;background:#EEF2FF;
                             border-radius:50%;text-align:center;
                             font-size:12px;font-weight:700;color:#4B7BF5;
                             vertical-align:top;padding-top:6px;">1</td>
                  <td style="padding-left:10px;font-size:13px;color:#6B7280;
                             padding-bottom:8px;">
                    QabiFly app ya website pe wapas jayein
                  </td>
                </tr>
                <tr>
                  <td style="width:28px;height:28px;background:#EEF2FF;
                             border-radius:50%;text-align:center;
                             font-size:12px;font-weight:700;color:#4B7BF5;
                             vertical-align:top;padding-top:6px;">2</td>
                  <td style="padding-left:10px;font-size:13px;color:#6B7280;
                             padding-bottom:8px;">
                    OTP box mein upar diya code enter karein
                  </td>
                </tr>
                <tr>
                  <td style="width:28px;height:28px;background:#EEF2FF;
                             border-radius:50%;text-align:center;
                             font-size:12px;font-weight:700;color:#4B7BF5;
                             vertical-align:top;padding-top:6px;">3</td>
                  <td style="padding-left:10px;font-size:13px;color:#6B7280;">
                    Login ho jayein aur shopping enjoy karein! 🎉
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- ── Divider ── -->
          <tr>
            <td style="padding:0 40px;">
              <hr style="border:none;border-top:1px solid #F3F4F6;margin:0;" />
            </td>
          </tr>

          <!-- ── Footer ── -->
          <tr>
            <td style="padding:20px 40px;text-align:center;">
              <p style="margin:0 0 6px;font-size:12px;color:#9CA3AF;">
                Agar aapne yeh request nahi ki toh is email ko ignore karein.
              </p>
              <p style="margin:0;font-size:11px;color:#D1D5DB;">
                © 2024 QabiFly · ZEAIPC ·
                <a href="https://qalbconverfy.in"
                   style="color:#6366F1;text-decoration:none;">
                  qalbconverfy.in
                </a>
                · Reoti, Ballia, UP
              </p>
            </td>
          </tr>

          <!-- ── Color bar ── -->
          <tr>
            <td style="height:5px;
                       background:linear-gradient(90deg,
                         #4B7BF5,#7C3AED,#EC4899,#F59E0B);"></td>
          </tr>

        </table>
        <!-- /Card -->

      </td>
    </tr>
  </table>

</body>
</html>"""

    try:
        msg = EmailMultiAlternatives(
            subject    = subject,
            body       = text_body,
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [to_email],
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
    items_list: list = None,
) -> bool:
    """Order confirmation email."""

    subject = f"✅ Order #{order_number} Confirm Ho Gaya — QabiFly"

    text_body = (
        f"Namaste {buyer_name},\n\n"
        f"Aapka order #{order_number} confirm ho gaya!\n"
        f"Total: Rs.{total}\n\n"
        f"App mein track karein.\n"
        f"— QabiFly Team"
    )

    logo_tag    = _logo_img_tag()
    items_html  = ""

    if items_list:
        for item in items_list:
            items_html += f"""
            <tr>
              <td style="padding:8px 0;font-size:13px;color:#374151;
                         border-bottom:1px solid #F3F4F6;">
                {item.get('name', '')} × {item.get('quantity', 1)}
              </td>
              <td style="padding:8px 0;font-size:13px;color:#374151;
                         text-align:right;border-bottom:1px solid #F3F4F6;
                         font-weight:600;">
                ₹{item.get('total', '')}
              </td>
            </tr>"""

    html_body = f"""<!DOCTYPE html>
<html lang="hi">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#EEF2FF;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="520" cellpadding="0" cellspacing="0"
               style="background:#fff;border-radius:20px;overflow:hidden;
                      box-shadow:0 8px 32px rgba(75,123,245,0.12);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#4B7BF5,#9333EA);
                       padding:28px 40px;text-align:center;">
              <div style="margin-bottom:10px;">{logo_tag}</div>
              <div style="color:#fff;font-size:24px;font-weight:800;">QabiFly</div>
              <div style="color:rgba(255,255,255,0.75);font-size:11px;margin-top:4px;">
                AAPKI ZARURAT HAMARI ZIMMEDARI
              </div>
            </td>
          </tr>

          <!-- Success Banner -->
          <tr>
            <td style="background:#F0FDF4;padding:20px 40px;text-align:center;
                       border-bottom:1px solid #D1FAE5;">
              <div style="font-size:36px;margin-bottom:6px;">✅</div>
              <div style="font-size:18px;font-weight:800;color:#166534;">
                Order Confirm Ho Gaya!
              </div>
              <div style="font-size:13px;color:#16A34A;margin-top:4px;">
                Aapka order successfully place ho gaya
              </div>
            </td>
          </tr>

          <!-- Order Info -->
          <tr>
            <td style="padding:28px 40px;">
              <p style="margin:0 0 6px;font-size:15px;color:#374151;">
                Namaste <strong style="color:#4B7BF5;">{buyer_name}</strong>! 👋
              </p>
              <p style="margin:0 0 20px;font-size:13px;color:#6B7280;">
                Aapke order ki details:
              </p>

              <!-- Order Number Box -->
              <div style="background:#EEF2FF;border:1.5px solid #C7D2FE;
                          border-radius:12px;padding:14px 20px;margin-bottom:20px;
                          display:flex;justify-content:space-between;
                          align-items:center;">
                <div>
                  <div style="font-size:10px;color:#6366F1;font-weight:700;
                              letter-spacing:1px;text-transform:uppercase;">
                    Order Number
                  </div>
                  <div style="font-size:18px;font-weight:800;color:#1E1B4B;
                              font-family:monospace;margin-top:2px;">
                    #{order_number}
                  </div>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:10px;color:#6366F1;font-weight:700;
                              letter-spacing:1px;text-transform:uppercase;">
                    Total
                  </div>
                  <div style="font-size:22px;font-weight:800;color:#4B7BF5;
                              margin-top:2px;">
                    ₹{total}
                  </div>
                </div>
              </div>

              <!-- Items -->
              {f'''
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="margin-bottom:20px;">
                <tr>
                  <td style="font-size:11px;font-weight:700;color:#9CA3AF;
                             letter-spacing:1px;text-transform:uppercase;
                             padding-bottom:8px;">Item</td>
                  <td style="font-size:11px;font-weight:700;color:#9CA3AF;
                             letter-spacing:1px;text-transform:uppercase;
                             text-align:right;padding-bottom:8px;">Amount</td>
                </tr>
                {items_html}
              </table>''' if items_html else ''}

            </td>
          </tr>

          <!-- Color bar -->
          <tr>
            <td style="height:5px;
                       background:linear-gradient(90deg,
                         #4B7BF5,#7C3AED,#EC4899,#F59E0B);"></td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:18px 40px;text-align:center;">
              <p style="margin:0;font-size:11px;color:#D1D5DB;">
                © 2024 QabiFly · ZEAIPC ·
                <a href="https://qalbconverfy.in"
                   style="color:#6366F1;text-decoration:none;">
                  qalbconverfy.in
                </a>
                · Reoti, Ballia, UP
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

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

from django.core.mail import EmailMultiAlternatives

LOGO_URL = "https://futrr.s3.us-east-1.amazonaws.com/email-assets/futrr-banner-transparent.png"

# Inline SVG icons encoded for email (avoids emoji / unicode issues)
ICON_CAPSULE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 24 24' fill='none' stroke='%23EAA646' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='18' height='18' rx='4'/%3E%3Cpath d='M3 12h18'/%3E%3Cpath d='M12 3v18'/%3E%3Ccircle cx='12' cy='12' r='2'/%3E%3C/svg%3E"
ICON_DISCOVER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 24 24' fill='none' stroke='%23EAA646' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpolygon points='16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76'/%3E%3C/svg%3E"
ICON_TIMELINE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 24 24' fill='none' stroke='%23EAA646' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpolyline points='12 6 12 12 16 14'/%3E%3C/svg%3E"


def send_welcome_email(email, username):
    subject = "Welcome to Futrr!"
    text = f"Hey {username}, welcome to Futrr! Start creating capsules and capture moments for the future."

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#F5F2ED;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F5F2ED;padding:40px 20px;">
    <tr><td align="center">
      <table role="presentation" width="520" cellpadding="0" cellspacing="0" style="background-color:#FFFFFF;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.06);">

        <!-- Logo -->
        <tr><td style="padding:20px 40px 0px;text-align:center;">
          <img src="{LOGO_URL}" alt="futrr" width="180" style="display:inline-block;" />
        </td></tr>

        <!-- Accent bar -->
        <tr><td style="padding:0 60px;"><div style="height:3px;border-radius:2px;background:linear-gradient(90deg,#EAA646,#E8924A);"></div></td></tr>

        <!-- Greeting -->
        <tr><td style="padding:32px 40px 0;text-align:center;">
          <h2 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#1A1A1A;">Welcome aboard, {username}!</h2>
          <p style="margin:0;font-size:15px;color:#6B6560;line-height:1.6;">
            We're thrilled to have you. Futrr is your personal time capsule &mdash; a place to capture memories, moments, and messages for the future.
          </p>
        </td></tr>

        <!-- Spacer -->
        <tr><td style="height:28px;"></td></tr>

        <!-- Feature 1: Capsules -->
        <tr><td style="padding:0 36px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FBF9F6;border-radius:14px;">
            <tr>
              <td style="width:56px;padding:18px 0 18px 18px;vertical-align:top;">
                <div style="width:44px;height:44px;border-radius:12px;background-color:#FDF3E4;text-align:center;line-height:44px;">
                  <img src="{ICON_CAPSULE}" width="24" height="24" alt="" style="display:inline-block;vertical-align:middle;" />
                </div>
              </td>
              <td style="padding:18px 18px 18px 14px;vertical-align:top;">
                <p style="margin:0 0 3px;font-size:15px;font-weight:600;color:#1A1A1A;">Create Capsules</p>
                <p style="margin:0;font-size:13px;color:#9B9590;line-height:1.45;">Write messages, add photos, videos, or audio &mdash; anything you want to preserve for the future.</p>
              </td>
            </tr>
          </table>
        </td></tr>

        <tr><td style="height:10px;"></td></tr>

        <!-- Feature 2: Discover -->
        <tr><td style="padding:0 36px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FBF9F6;border-radius:14px;">
            <tr>
              <td style="width:56px;padding:18px 0 18px 18px;vertical-align:top;">
                <div style="width:44px;height:44px;border-radius:12px;background-color:#FDF3E4;text-align:center;line-height:44px;">
                  <img src="{ICON_DISCOVER}" width="24" height="24" alt="" style="display:inline-block;vertical-align:middle;" />
                </div>
              </td>
              <td style="padding:18px 18px 18px 14px;vertical-align:top;">
                <p style="margin:0 0 3px;font-size:15px;font-weight:600;color:#1A1A1A;">Discover &amp; Connect</p>
                <p style="margin:0;font-size:13px;color:#9B9590;line-height:1.45;">Explore public capsules, find friends, and unlock shared memories together.</p>
              </td>
            </tr>
          </table>
        </td></tr>

        <tr><td style="height:10px;"></td></tr>

        <!-- Feature 3: Timeline -->
        <tr><td style="padding:0 36px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FBF9F6;border-radius:14px;">
            <tr>
              <td style="width:56px;padding:18px 0 18px 18px;vertical-align:top;">
                <div style="width:44px;height:44px;border-radius:12px;background-color:#FDF3E4;text-align:center;line-height:44px;">
                  <img src="{ICON_TIMELINE}" width="24" height="24" alt="" style="display:inline-block;vertical-align:middle;" />
                </div>
              </td>
              <td style="padding:18px 18px 18px 14px;vertical-align:top;">
                <p style="margin:0 0 3px;font-size:15px;font-weight:600;color:#1A1A1A;">Your Timeline</p>
                <p style="margin:0;font-size:13px;color:#9B9590;line-height:1.45;">Every capsule lands on your timeline &mdash; past, present, and future at a glance.</p>
              </td>
            </tr>
          </table>
        </td></tr>

        <!-- CTA -->
        <tr><td style="padding:28px 40px 0;text-align:center;">
          <p style="margin:0;font-size:15px;color:#6B6560;line-height:1.5;">Open the app and create your first capsule.<br/>The future is waiting.</p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:28px 40px 36px;text-align:center;">
          <div style="height:1px;background-color:#E8E4DE;margin-bottom:18px;"></div>
          <p style="margin:0;font-size:11px;color:#B5B0AA;letter-spacing:0.3px;">Futrr &mdash; Capture moments, unlock the future.</p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email="Futrr <no-reply@futrr.app>",
        to=[email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)

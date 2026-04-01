from django.core.mail import EmailMultiAlternatives

LOGO_URL = "https://futrr.s3.us-east-1.amazonaws.com/email-assets/futrr-banner-transparent.png"
ICON_CAPSULE = "https://futrr.s3.us-east-1.amazonaws.com/email-assets/icon-capsule.png"
ICON_GLOBE = "https://futrr.s3.us-east-1.amazonaws.com/email-assets/icon-globe.png"
ICON_TIMELINE = "https://futrr.s3.us-east-1.amazonaws.com/email-assets/icon-timeline.png"


def _feature_row(icon_url, title, body):
    return f"""<tr><td style="padding:0 36px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#FBF9F6;border-radius:14px;">
    <tr>
      <td style="width:62px;padding:16px 0 16px 16px;vertical-align:top;">
        <img src="{icon_url}" alt="" width="44" height="44" style="display:block;border-radius:12px;" />
      </td>
      <td style="padding:16px 18px 16px 14px;vertical-align:top;">
        <p style="margin:0 0 3px;font-size:15px;font-weight:600;color:#1A1A1A;">{title}</p>
        <p style="margin:0;font-size:13px;color:#9B9590;line-height:1.45;">{body}</p>
      </td>
    </tr>
  </table>
</td></tr>
<tr><td style="height:10px;"></td></tr>"""


def send_welcome_email(email, username):
    subject = "Welcome to Futrr!"
    text = f"Hey {username}, welcome to Futrr! Start creating capsules and capture moments for the future."

    features = (
        _feature_row(
            ICON_CAPSULE,
            "Create Capsules",
            "Write messages, add photos, videos, or audio &mdash; anything you want to preserve for the future.",
        )
        + _feature_row(
            ICON_GLOBE,
            "Discover &amp; Connect",
            "Explore public capsules, find friends, and unlock shared memories together.",
        )
        + _feature_row(
            ICON_TIMELINE,
            "Your Timeline",
            "Every capsule lands on your timeline &mdash; past, present, and future at a glance.",
        )
    )

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
        <tr><td style="padding:0 60px;"><div style="height:3px;border-radius:2px;background:#EAA646;"></div></td></tr>

        <!-- Greeting -->
        <tr><td style="padding:32px 40px 0;text-align:center;">
          <h2 style="margin:0 0 8px;font-size:24px;font-weight:700;color:#1A1A1A;">Welcome aboard, {username}!</h2>
          <p style="margin:0;font-size:15px;color:#6B6560;line-height:1.6;">
            We're thrilled to have you. Futrr is your personal time capsule &mdash; a place to capture memories, moments, and messages for the future.
          </p>
        </td></tr>

        <!-- Spacer -->
        <tr><td style="height:28px;"></td></tr>

        <!-- Feature cards -->
        {features}

        <!-- CTA -->
        <tr><td style="padding:18px 40px 0;text-align:center;">
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

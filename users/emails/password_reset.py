from django.core.mail import EmailMultiAlternatives

LOGO_URL = "https://futrr.s3.us-east-1.amazonaws.com/email-assets/futrr-banner-transparent.png"


def send_password_reset_confirmation_email(email, username):
    subject = "Your Futrr password was reset"
    text = f"Hi {username}, your password was successfully changed. If this wasn't you, please contact us immediately."

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

        <!-- Icon -->
        <tr><td style="padding:28px 40px 0;text-align:center;">
          <div style="display:inline-block;width:56px;height:56px;border-radius:28px;background-color:#E8F5E9;line-height:56px;text-align:center;font-size:28px;">&#10003;</div>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:20px 40px 0;text-align:center;">
          <h2 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#1A1A1A;">Password Changed</h2>
          <p style="margin:0;font-size:15px;color:#6B6560;line-height:1.6;">
            Hi <strong>{username}</strong>, your Futrr password was successfully reset. You can now log in with your new password.
          </p>
        </td></tr>

        <!-- Security note -->
        <tr><td style="padding:24px 48px 0;text-align:center;">
          <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="background-color:#FFF8F0;border-radius:12px;border:1px solid #F0E0CC;"><tr>
            <td style="padding:14px 20px;">
              <p style="margin:0;font-size:13px;color:#9B7A54;line-height:1.5;">If you didn't make this change, please reset your password immediately or contact us at <strong>contact@futrr.app</strong></p>
            </td>
          </tr></table>
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

from django.core.mail import EmailMultiAlternatives

LOGO_URL = "https://futrr.s3.us-east-1.amazonaws.com/email-assets/futrr-banner-transparent.png"


def send_otp_email(email, otp):
    subject = "Your Futrr verification code"
    text = f"Your verification code is {otp}. It expires in 10 minutes."
    digits = list(str(otp))

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

        <!-- Heading -->
        <tr><td style="padding:32px 40px 8px;text-align:center;">
          <p style="margin:0;font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:2px;color:#C4956E;">Verification Code</p>
        </td></tr>

        <!-- OTP digits -->
        <tr><td style="padding:16px 40px 8px;text-align:center;">
          <table role="presentation" cellpadding="0" cellspacing="0" align="center"><tr>
            {''.join(f'<td style="padding:0 4px;"><div style="width:46px;height:56px;line-height:56px;text-align:center;font-size:28px;font-weight:700;color:#1A1A1A;background-color:#FAF8F5;border:2px solid #E8E4DE;border-radius:12px;">{d}</div></td>' for d in digits)}
          </tr></table>
        </td></tr>

        <!-- Timer icon + expiry -->
        <tr><td style="padding:20px 40px 0;text-align:center;">
          <table role="presentation" cellpadding="0" cellspacing="0" align="center"><tr>
            <td style="vertical-align:middle;padding-right:8px;">
              <!-- Hourglass SVG -->
              <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%23C4956E' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 22h14'/%3E%3Cpath d='M5 2h14'/%3E%3Cpath d='M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22'/%3E%3Cpath d='M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2'/%3E%3C/svg%3E" width="20" height="20" alt="" style="display:block;" />
            </td>
            <td style="vertical-align:middle;">
              <p style="margin:0;font-size:13px;color:#9B9590;">Expires in <strong style="color:#C4956E;">10 minutes</strong></p>
            </td>
          </tr></table>
        </td></tr>

        <!-- Security note -->
        <tr><td style="padding:24px 48px 0;text-align:center;">
          <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="background-color:#FBF9F6;border-radius:12px;padding:14px 20px;"><tr>
            <td style="vertical-align:middle;padding-right:10px;">
              <!-- Shield SVG -->
              <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%239B9590' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/%3E%3Cpath d='m9 12 2 2 4-4'/%3E%3C/svg%3E" width="18" height="18" alt="" style="display:block;" />
            </td>
            <td style="vertical-align:middle;">
              <p style="margin:0;font-size:12px;color:#9B9590;line-height:1.4;">If you didn't request this code, you can safely ignore this email.</p>
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

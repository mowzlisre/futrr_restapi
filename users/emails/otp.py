from django.core.mail import EmailMultiAlternatives

LOGO_URL = "https://futrr.s3.us-east-1.amazonaws.com/email-assets/futrr-banner-transparent.png"


def send_otp_email(email, otp, purpose="verify"):
    """Send OTP email. purpose: 'verify' for signup, 'reset' for password reset."""
    if purpose == "reset":
        subject = "Reset your Futrr password"
        heading = "Password Reset Code"
        context_line = "Use this code to reset your password."
    else:
        subject = "Your Futrr verification code"
        heading = "Verification Code"
        context_line = "Use this code to verify your email address."

    text = f"Your code is {otp}. It expires in 10 minutes. {context_line}"
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
        <tr><td style="padding:0 60px;"><div style="height:3px;border-radius:2px;background:#EAA646;"></div></td></tr>

        <!-- Heading -->
        <tr><td style="padding:32px 40px 4px;text-align:center;">
          <p style="margin:0;font-size:14px;font-weight:600;text-transform:uppercase;letter-spacing:2px;color:#C4956E;">{heading}</p>
          <p style="margin:6px 0 0;font-size:13px;color:#9B9590;">{context_line}</p>
        </td></tr>

        <!-- OTP digits -->
        <tr><td style="padding:16px 40px 8px;text-align:center;">
          <table role="presentation" cellpadding="0" cellspacing="0" align="center"><tr>
            {''.join(f'<td style="padding:0 4px;"><div style="width:46px;height:56px;line-height:56px;text-align:center;font-size:28px;font-weight:700;color:#1A1A1A;background-color:#FAF8F5;border:2px solid #E8E4DE;border-radius:12px;">{d}</div></td>' for d in digits)}
          </tr></table>
        </td></tr>

        <!-- Timer + expiry -->
        <tr><td style="padding:20px 40px 0;text-align:center;">
          <table role="presentation" cellpadding="0" cellspacing="0" align="center"><tr>
            <td style="vertical-align:middle;padding-right:8px;">
              <div style="width:20px;height:20px;border-radius:10px;border:2px solid #C4956E;text-align:center;line-height:18px;font-size:11px;color:#C4956E;font-weight:700;">&#8986;</div>
            </td>
            <td style="vertical-align:middle;">
              <p style="margin:0;font-size:13px;color:#9B9590;">Expires in <strong style="color:#C4956E;">10 minutes</strong></p>
            </td>
          </tr></table>
        </td></tr>

        <!-- Security note -->
        <tr><td style="padding:24px 48px 0;text-align:center;">
          <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="background-color:#FBF9F6;border-radius:12px;"><tr>
            <td style="padding:14px 20px;">
              <table role="presentation" cellpadding="0" cellspacing="0"><tr>
                <td style="vertical-align:middle;padding-right:10px;">
                  <div style="width:22px;height:22px;border-radius:11px;background-color:#E8E4DE;text-align:center;line-height:22px;font-size:12px;color:#9B9590;font-weight:700;">&#10003;</div>
                </td>
                <td style="vertical-align:middle;">
                  <p style="margin:0;font-size:12px;color:#9B9590;line-height:1.4;">If you didn't request this code, you can safely ignore this email.</p>
                </td>
              </tr></table>
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

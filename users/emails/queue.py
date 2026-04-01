import logging
from django.utils import timezone
from users.models import EmailQueue
from .otp import send_otp_email
from .welcome import send_welcome_email
from .password_reset import send_password_reset_confirmation_email

email_logger = logging.getLogger("futrr.email")

# Map email_type → (send_function, args_extractor)
_DISPATCH = {
    "signup_otp": lambda p: send_otp_email(p["email"], p["otp"], purpose="verify"),
    "reset_otp": lambda p: send_otp_email(p["email"], p["otp"], purpose="reset"),
    "reset_confirm": lambda p: send_password_reset_confirmation_email(p["email"], p["username"]),
    "welcome": lambda p: send_welcome_email(p["email"], p["username"]),
}


def enqueue_email(recipient, email_type, priority, payload):
    """Add an email to the queue."""
    entry = EmailQueue.objects.create(
        recipient=recipient,
        email_type=email_type,
        priority=priority,
        payload=payload,
    )
    email_logger.info("email_queued", extra={
        "action": "email_queued",
        "email": recipient,
        "email_type": email_type,
        "priority": priority,
    })
    return entry


def send_queued_email(entry):
    """Dispatch a queued email entry. Returns True on success."""
    dispatch_fn = _DISPATCH.get(entry.email_type)
    if not dispatch_fn:
        entry.status = EmailQueue.Status.FAILED
        entry.error = f"Unknown email_type: {entry.email_type}"
        entry.save(update_fields=["status", "error"])
        return False

    entry.attempts += 1
    try:
        dispatch_fn(entry.payload)
        entry.status = EmailQueue.Status.SENT
        entry.sent_at = timezone.now()
        entry.save(update_fields=["status", "sent_at", "attempts"])
        email_logger.info("email_sent", extra={
            "action": "email_sent",
            "email": entry.recipient,
            "email_type": entry.email_type,
        })
        return True
    except Exception as e:
        entry.error = str(e)
        if entry.attempts >= 3:
            entry.status = EmailQueue.Status.FAILED
        entry.save(update_fields=["status", "attempts", "error"])
        email_logger.error("email_send_failed", extra={
            "action": "email_send_failed",
            "email": entry.recipient,
            "email_type": entry.email_type,
            "error": str(e),
            "attempts": entry.attempts,
        })
        return False

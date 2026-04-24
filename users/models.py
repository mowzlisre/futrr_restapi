from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid
import secrets
from django.utils import timezone
from datetime import timedelta


class FutrrUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        if not username:
            raise ValueError("Username must be provided")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, username, password, **extra_fields)


class FutrrUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=30, unique=True, db_index=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)

    isPreboarded = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)

    avatar = models.TextField(blank=True, null=True)
    bio = models.TextField(max_length=300, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    notification_email = models.BooleanField(default=True)
    notification_push = models.BooleanField(default=True)
    notify_capsule_created = models.BooleanField(default=True)
    notify_friend_request = models.BooleanField(default=True)
    notify_capsule_unlocked = models.BooleanField(default=True)
    notify_capsule_shared = models.BooleanField(default=True)
    notify_nearby_capsule = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = FutrrUserManager()

    def __str__(self):
        return self.username

    @property
    def capsules_sealed(self):
        return self.capsules_created.filter(status="sealed").count()

    @property
    def capsules_unlocked(self):
        return self.capsules_created.filter(status="unlocked").count()


class PasswordResetToken(models.Model):
    """Temporary tokens for password reset"""
    user = models.ForeignKey(FutrrUser, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=255, unique=True, default=secrets.token_urlsafe)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset token for {self.user.email}"

    def is_valid(self):
        """Check if token is still valid and not used"""
        return not self.is_used and timezone.now() < self.expires_at

    def save(self, *args, **kwargs):
        """Set expiration time to 1 hour from creation"""
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)


class Follow(models.Model):
    """follower → following relationship (Twitter-style, no mutual approval)."""
    follower = models.ForeignKey(
        FutrrUser, on_delete=models.CASCADE, related_name="following"
    )
    following = models.ForeignKey(
        FutrrUser, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["follower", "following"]]

    def __str__(self):
        return f"{self.follower} → {self.following}"


class FollowRequest(models.Model):
    """Pending follow request when target account is private."""
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
    ]

    from_user = models.ForeignKey(
        FutrrUser, on_delete=models.CASCADE, related_name="sent_follow_requests"
    )
    to_user = models.ForeignKey(
        FutrrUser, on_delete=models.CASCADE, related_name="received_follow_requests"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["from_user", "to_user"]]

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"


class TwoFactorDevice(models.Model):
    """2FA devices for users"""
    DEVICE_TYPES = [
        ('totp', 'Time-based OTP'),
        ('sms', 'SMS'),
        ('email', 'Email'),
    ]

    user = models.ForeignKey(FutrrUser, on_delete=models.CASCADE, related_name='two_factor_devices')
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    device_name = models.CharField(max_length=100, help_text="e.g., iPhone 12, Google Authenticator")
    secret = models.CharField(max_length=255, default=secrets.token_urlsafe)  # For TOTP
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'device_name')
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.device_type} ({self.device_name})"


class EmailOTP(models.Model):
    """Short-lived OTP for email verification during registration."""
    email = models.EmailField(db_index=True)
    otp = models.CharField(max_length=6)
    session_token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def save(self, *args, **kwargs):
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OTP for {self.email}"


class EmailQueue(models.Model):
    """Queue for outbound emails with priority-based delivery."""

    class Priority(models.TextChoices):
        HIGH = "high", "High"    # OTP, password reset
        LOW = "low", "Low"       # welcome, reset confirmation

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    recipient = models.EmailField()
    email_type = models.CharField(max_length=30)  # signup_otp, reset_otp, reset_confirm, welcome
    priority = models.CharField(max_length=4, choices=Priority.choices)
    payload = models.JSONField(default=dict)       # {otp, username, purpose, etc.}
    status = models.CharField(max_length=7, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    attempts = models.IntegerField(default=0)
    error = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "priority", "created_at"]),
        ]

    def __str__(self):
        return f"{self.email_type} → {self.recipient} ({self.status})"


class UserQuota(models.Model):
    """Per-user usage limits. Created automatically on signup with free-tier defaults."""

    user = models.OneToOneField(FutrrUser, on_delete=models.CASCADE, related_name="quota")

    # Limits (NULL = unlimited)
    max_event_participants = models.PositiveIntegerField(default=200)
    max_capsule_recipients = models.PositiveIntegerField(default=5)

    tier = models.CharField(max_length=20, default="free")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — {self.tier}"


class SupportTicket(models.Model):
    """User-submitted support / upgrade requests visible in admin panel."""

    class Category(models.TextChoices):
        UPGRADE = "upgrade", "Upgrade Request"
        BUG = "bug", "Bug Report"
        GENERAL = "general", "General"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(FutrrUser, on_delete=models.CASCADE, related_name="support_tickets")
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.GENERAL)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.category}] {self.subject} — {self.user.username}"


class Subscription(models.Model):
    """
    Single source of truth for every user's plan limits.
    Free tier = default values.  Admin overrides → 'free+'.
    Future paid plans override everything and set an expiry.
    """

    TIER_CHOICES = [
        ("free", "Free"),
        ("free+", "Free+"),
        ("pro", "Pro"),
        ("enterprise", "Enterprise"),
    ]

    user = models.OneToOneField(
        FutrrUser, on_delete=models.CASCADE, related_name="subscription"
    )
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default="free")

    # Weekly limits (reset every Monday 00:00 UTC)
    max_capsules_per_week = models.PositiveIntegerField(default=5)
    max_events_per_week = models.PositiveIntegerField(default=1)

    # Per-item limits
    max_event_participants = models.PositiveIntegerField(default=200)
    max_recipients_per_capsule = models.PositiveIntegerField(default=5)
    max_media_per_capsule = models.PositiveIntegerField(default=10)

    # Atlas
    atlas_radius_miles = models.FloatField(default=1.0)
    atlas_radius_growth = models.FloatField(default=0.5)  # extra miles gained per week

    # Storage (MB)
    max_storage_mb = models.PositiveIntegerField(default=100)

    # Favourites
    max_favorites = models.PositiveIntegerField(default=25)

    # Lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # null → never expires

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        exp = f" (expires {self.expires_at:%Y-%m-%d})" if self.expires_at else ""
        return f"{self.user.username} — {self.tier}{exp}"

    @property
    def is_active(self):
        if self.expires_at is None:
            return True
        return timezone.now() < self.expires_at
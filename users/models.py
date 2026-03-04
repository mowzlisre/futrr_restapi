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

    avatar = models.TextField(blank=True, null=True)
    bio = models.TextField(max_length=300, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    notification_email = models.BooleanField(default=True)
    notification_push = models.BooleanField(default=True)
    capsules_sealed = models.PositiveIntegerField(default=0)
    capsules_unlocked = models.PositiveIntegerField(default=0)
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
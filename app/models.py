import uuid
from django.db import models
from django.utils import timezone
from users.models import FutrrUser


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    banner_image = models.CharField(max_length=500, blank=True)  # S3 key for event banner
    created_by = models.ForeignKey(
        FutrrUser, on_delete=models.SET_NULL, null=True, related_name="events_created"
    )
    # unlock_at is only required for time-locked events
    unlock_at = models.DateTimeField(null=True, blank=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True, null=True)
    invite_token = models.UUIDField(default=uuid.uuid4, unique=True)
    EVENT_TYPE_CHOICES = [
        ("birthday", "Birthday"),
        ("wedding", "Wedding"),
        ("graduation", "Graduation"),
        ("anniversary", "Anniversary"),
        ("new_year", "New Year"),
        ("sports", "Sports"),
        ("travel", "Travel"),
        ("festival", "Festival"),
        ("music", "Music"),
        ("memorial", "Memorial"),
        ("reunion", "Reunion"),
        ("other", "Other"),
    ]
    is_public = models.BooleanField(default=False, db_index=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES, default="other")
    # Editable display label for the event type (overrides the default label)
    event_type_label = models.CharField(max_length=100, blank=True)
    # Time-locked: capsules sealed until unlock_at; Open: capsules accessible anytime
    is_time_locked = models.BooleanField(default=True)
    # Window during which participants can submit capsules
    entry_start = models.DateTimeField(null=True, blank=True)
    entry_close = models.DateTimeField(null=True, blank=True)
    # Max number of participants (null = unlimited)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    # Which content types participants are allowed to submit: ["text","photo","video","voice"]
    allowed_content_types = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.title


class Capsule(models.Model):

    class Status(models.TextChoices):
        SEALED = "sealed", "Sealed"
        UNLOCKED = "unlocked", "Unlocked"
        EXPIRED = "expired", "Expired"
        BROKEN = "broken", "Broken"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SEALED, db_index=True
    )

    created_by = models.ForeignKey(
        FutrrUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="capsules_created",
    )

    recipients = models.ManyToManyField(
        FutrrUser,
        through="CapsuleRecipient",
        related_name="capsules_received",
        blank=True,
    )

    is_public = models.BooleanField(default=False, db_index=True)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)

    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="capsules",
    )

    sealed_at = models.DateTimeField(default=timezone.now)
    unlock_at = models.DateTimeField()
    unlocked_at = models.DateTimeField(null=True, blank=True)

    # Optional location lock
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True)
    unlock_radius_meters = models.PositiveIntegerField(default=100)

    # Optional hint shown to the recipient at unlock time (not the passphrase itself)
    passphrase_hint = models.CharField(max_length=200, blank=True)

    # Whether the capsule is listed on the Atlas map (only relevant for public capsules)
    listed_in_atlas = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    @property
    def capsule_type(self):
        if self.is_public:
            return "public"
        elif self.capsule_recipients.exists():
            return "private"
        else:
            return "self"

    @property
    def is_accessible(self):
        return self.status != self.Status.BROKEN

    @property
    def is_ready_to_unlock(self):
        if not self.is_accessible:
            return False
        return timezone.now() >= self.unlock_at and self.status == self.Status.SEALED

    def unlock(self):
        if not self.is_accessible:
            raise PermissionError("This capsule is broken and cannot be unlocked.")
        if self.is_ready_to_unlock:
            self.status = self.Status.UNLOCKED
            self.unlocked_at = timezone.now()
            self.save(update_fields=["status", "unlocked_at"])


class CapsuleRecipient(models.Model):

    class AddedVia(models.TextChoices):
        INVITED = "invited", "Invited"
        LINK = "link", "Link"
        PUBLIC = "public", "Public"

    capsule = models.ForeignKey(
        Capsule, on_delete=models.CASCADE, related_name="capsule_recipients"
    )
    user = models.ForeignKey(
        FutrrUser, on_delete=models.SET_NULL, null=True, blank=True
    )
    email = models.EmailField(blank=True)
    added_via = models.CharField(
        max_length=20, choices=AddedVia.choices, default=AddedVia.INVITED
    )
    has_opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [["capsule", "user"], ["capsule", "email"]]

    def __str__(self):
        return f"{self.capsule_id} → {self.user or self.email}"


class CapsuleContent(models.Model):

    class ContentType(models.TextChoices):
        TEXT = "text", "Text Note"
        PHOTO = "photo", "Photo"
        VOICE = "voice", "Voice Note"
        VIDEO = "video", "Video"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capsule = models.ForeignKey(
        Capsule, on_delete=models.CASCADE, related_name="contents"
    )
    added_by = models.ForeignKey(
        FutrrUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="contributions",
    )
    content_type = models.CharField(max_length=10, choices=ContentType.choices)

    body = models.TextField(blank=True)  # TEXT content (ciphertext)

    # Stores the S3 object key, e.g. "capsule_media/abc-123/voice_xyz.mp3"
    # Never a local file path — always the raw S3 key
    file = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)  # bytes
    duration = models.PositiveIntegerField(null=True, blank=True)  # seconds (audio/video)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content_type} in {self.capsule_id}"


class CapsuleFavorite(models.Model):
    user = models.ForeignKey(
        FutrrUser, on_delete=models.CASCADE, related_name="favorite_capsules"
    )
    capsule = models.ForeignKey(
        Capsule, on_delete=models.CASCADE, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "capsule"]]

    def __str__(self):
        return f"{self.user_id} ♡ {self.capsule_id}"


class CapsulePin(models.Model):
    """
    A user pins a public capsule to their own profile.
    Only public capsules can be pinned.  When a capsule goes private,
    all its pins are auto-deleted.
    """
    user = models.ForeignKey(
        FutrrUser, on_delete=models.CASCADE, related_name="pinned_capsules"
    )
    capsule = models.ForeignKey(
        Capsule, on_delete=models.CASCADE, related_name="pinned_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "capsule"]]

    def __str__(self):
        return f"{self.user_id} 📌 {self.capsule_id}"


class Notification(models.Model):

    class NotifType(models.TextChoices):
        CAPSULE_UNLOCKED = "capsule_unlocked", "Capsule Unlocked"
        RECIPIENT_ADDED = "recipient_added", "Added as Recipient"
        EVENT_JOINED = "event_joined", "Someone Joined Your Event"
        EVENT_UNLOCKED = "event_unlocked", "Event Capsules Unlocked"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        FutrrUser, on_delete=models.CASCADE, related_name="notifications"
    )
    notif_type = models.CharField(max_length=30, choices=NotifType.choices)
    title = models.CharField(max_length=120)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    related_capsule = models.ForeignKey(
        Capsule, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications"
    )
    related_event = models.ForeignKey(
        Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.notif_type} → {self.user_id}"


class CapsuleEncryptionKey(models.Model):

    class KeyStrategy(models.TextChoices):
        UMK = "umk", "User Maintained Key"
        SMK = "smk", "System Maintained Key"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capsule = models.OneToOneField(
        Capsule, on_delete=models.CASCADE, related_name="encryption_key"
    )
    user = models.ForeignKey(
        FutrrUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="encryption_keys",
    )
    strategy = models.CharField(max_length=10, choices=KeyStrategy.choices)
    encrypted_cek = models.BinaryField()
    kek_nonce = models.BinaryField()
    key_verifier = models.BinaryField(null=True, blank=True)  # UMK only
    kdf_salt = models.BinaryField(null=True, blank=True)  # UMK only
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.strategy.upper()} key for {self.capsule_id}"

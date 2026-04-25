import hashlib
import hmac as hmac_mod
import logging
import uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Capsule, CapsuleContent, CapsuleEncryptionKey, CapsuleFavorite, CapsuleRecipient, Event, Notification
from .s3 import generate_presigned_url, upload_encrypted_media, upload_file
from users.models import FutrrUser, Subscription

api_logger = logging.getLogger("futrr.api")
s3_logger = logging.getLogger("futrr.s3")


# ── Subscription helper ──────────────────────────────────────────────────────

_FREE_DEFAULTS = {
    "max_capsules_per_week": 5,
    "max_events_per_week": 1,
    "max_event_participants": 200,
    "max_recipients_per_capsule": 5,
    "max_media_per_capsule": 10,
    "atlas_radius_miles": 1.0,
    "atlas_radius_growth": 0.5,
    "max_storage_mb": 100,
    "max_favorites": 25,
}


def _get_sub(user):
    """Return the user's Subscription, creating free-tier defaults if absent.
    If the subscription has expired, return an object with free-tier values."""
    sub, _ = Subscription.objects.get_or_create(user=user)
    if not sub.is_active:
        # Expired — serve free defaults without persisting
        for k, v in _FREE_DEFAULTS.items():
            setattr(sub, k, v)
        sub.tier = "free"
    return sub


def _week_start():
    """Return Monday 00:00:00 UTC of the current week."""
    from datetime import timedelta
    now = timezone.now()
    return (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def _verify_passphrase(passphrase: str, enc_key) -> bool:
    """
    Verify a UMK passphrase against the PBKDF2-derived key verifier stored on
    the encryption key record.

    key_verifier stores the raw PBKDF2-HMAC-SHA256 output derived from the
    passphrase + kdf_salt.  We re-derive and compare using a constant-time
    comparison to prevent timing attacks.
    """
    salt = bytes(enc_key.kdf_salt)
    verifier = bytes(enc_key.key_verifier)
    derived = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 600_000)
    return hmac_mod.compare_digest(derived, verifier)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _presign_creator_avatar(avatar_value):
    """Presign S3-key avatars; pass through external URLs unchanged."""
    if avatar_value and avatar_value.startswith("user_avatars/"):
        return generate_presigned_url(avatar_value, expiry_seconds=3600)
    return avatar_value

def _serialize_capsule(capsule, include_content=False, user=None, favorited_ids=None):
    # Determine encryption type from the linked key record (if any).
    # "self" means UMK (passphrase-protected); "auto" means SMK or no key.
    try:
        enc_key = capsule.encryption_key
        encryption_type = (
            "self"
            if enc_key.strategy == CapsuleEncryptionKey.KeyStrategy.UMK
            else "auto"
        )
    except CapsuleEncryptionKey.DoesNotExist:
        encryption_type = "auto"

    # is_favorited: use pre-fetched set when available, otherwise hit the DB once.
    if favorited_ids is not None:
        is_favorited = capsule.id in favorited_ids
    elif user is not None:
        is_favorited = CapsuleFavorite.objects.filter(user=user, capsule=capsule).exists()
    else:
        is_favorited = False

    # Aggregate counts
    favorite_count = capsule.favorited_by.count()

    # Lightweight content-type summary (distinct types present in the capsule)
    content_types = list(
        capsule.contents.order_by().values_list("content_type", flat=True).distinct()
    ) if hasattr(capsule, '_prefetched_objects_cache') and 'contents' in capsule._prefetched_objects_cache else list(
        capsule.contents.order_by().values_list("content_type", flat=True).distinct()
    )

    data = {
        "id": str(capsule.id),
        "title": capsule.title,
        "description": capsule.description,
        "status": capsule.status,
        "capsule_type": capsule.capsule_type,
        "encryption_type": encryption_type,
        "is_public": capsule.is_public,
        "is_favorited": is_favorited,
        "listed_in_atlas": capsule.listed_in_atlas,
        "favorite_count": favorite_count,
        "share_token": str(capsule.share_token),
        "event": str(capsule.event_id) if capsule.event_id else None,
        "sealed_at": capsule.sealed_at,
        "unlock_at": capsule.unlock_at,
        "unlocked_at": capsule.unlocked_at,
        "latitude": capsule.latitude,
        "longitude": capsule.longitude,
        "location_name": capsule.location_name,
        "unlock_radius_meters": capsule.unlock_radius_meters,
        "content_types": content_types,
        "created_at": capsule.created_at,
        "created_by": str(capsule.created_by_id) if capsule.created_by_id else None,
        "created_by_username": capsule.created_by.username if capsule.created_by else None,
        "created_by_avatar": _presign_creator_avatar(capsule.created_by.avatar if capsule.created_by else None),
        "passphrase_hint": capsule.passphrase_hint,
    }
    if include_content:
        data["contents"] = [_serialize_content(c) for c in capsule.contents.all()]
    return data


def _serialize_content(content):
    data = {
        "id": str(content.id),
        "content_type": content.content_type,
        "created_at": content.created_at,
    }
    if content.content_type == CapsuleContent.ContentType.TEXT:
        data["body"] = content.body
    else:
        # Pre-signed URL only generated after confirming capsule is UNLOCKED
        data["url"] = generate_presigned_url(content.file) if content.file else None
        data["file_size"] = content.file_size
        data["duration"] = content.duration
    return data


def _serialize_event(event, user=None):
    capsules_qs = event.capsules.select_related("created_by")
    participant_count = capsules_qs.count()

    # Build participants list (first 5 for avatar stack)
    participants = []
    for c in capsules_qs[:5]:
        if c.created_by:
            participants.append({
                "id": str(c.created_by.id),
                "username": c.created_by.username,
            })

    data = {
        "id": str(event.id),
        "title": event.title,
        "subtitle": event.subtitle,
        "description": event.description,
        "slug": event.slug or None,
        "banner_image": generate_presigned_url(event.banner_image, expiry_seconds=3600) if event.banner_image else None,
        "created_by": str(event.created_by_id) if event.created_by_id else None,
        "created_by_username": event.created_by.username if event.created_by else None,
        "unlock_at": event.unlock_at,
        "invite_token": str(event.invite_token),
        "is_public": event.is_public,
        "event_type": event.event_type,
        "event_type_label": event.event_type_label,
        "is_time_locked": event.is_time_locked,
        "entry_start": event.entry_start,
        "entry_close": event.entry_close,
        "max_participants": event.max_participants,
        "allowed_content_types": event.allowed_content_types,
        "participant_count": participant_count,
        "participants": participants,
        "created_at": event.created_at,
    }

    # Check if requesting user already has a capsule in this event
    if user:
        data["user_has_capsule"] = capsules_qs.filter(created_by=user).exists()

    return data


# ---------------------------------------------------------------------------
# Capsules
# ---------------------------------------------------------------------------

class CapsuleListCreateView(APIView):
    """
    GET  /api/capsules/  — list all capsules the user created or received
    POST /api/capsules/  — create a new sealed capsule
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        created = Capsule.objects.filter(created_by=request.user).select_related("created_by", "encryption_key").prefetch_related("capsule_recipients")
        received = request.user.capsules_received.all().select_related("created_by", "encryption_key").prefetch_related("capsule_recipients")
        seen = set()
        capsules = []
        for c in list(created) + list(received):
            if c.id not in seen:
                seen.add(c.id)
                capsules.append(c)
        fav_ids = set(
            CapsuleFavorite.objects.filter(
                user=request.user, capsule_id__in=[c.id for c in capsules]
            ).values_list("capsule_id", flat=True)
        )
        return Response([_serialize_capsule(c, user=request.user, favorited_ids=fav_ids) for c in capsules])

    def post(self, request):
        unlock_at = request.data.get("unlock_at")

        event_id = request.data.get("event_id")
        event_obj = None
        if event_id:
            try:
                event_obj = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
            # Check if user already has a capsule in this event
            if Capsule.objects.filter(event=event_obj, created_by=request.user).exists():
                return Response(
                    {"error": "You already have a capsule in this event"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Use event's unlock_at for time-locked events
            if event_obj.is_time_locked and event_obj.unlock_at:
                unlock_at = event_obj.unlock_at.isoformat()
            elif not event_obj.is_time_locked:
                # Open events don't need unlock_at - set a far future date
                unlock_at = unlock_at or "2099-12-31T23:59:59Z"

        if not unlock_at:
            return Response(
                {"error": "unlock_at is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Quota: weekly capsule limit ──
        sub = _get_sub(request.user)
        capsules_this_week = Capsule.objects.filter(
            created_by=request.user, created_at__gte=_week_start()
        ).count()
        if capsules_this_week >= sub.max_capsules_per_week:
            return Response(
                {
                    "error": "Weekly capsule limit reached",
                    "limit": sub.max_capsules_per_week,
                    "current": capsules_this_week,
                    "tier": sub.tier,
                    "resets": "monday",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        capsule = Capsule.objects.create(
            title=request.data.get("title", ""),
            description=request.data.get("description", ""),
            created_by=request.user,
            event=event_obj,
            unlock_at=unlock_at,
            is_public=request.data.get("is_public", False),
            latitude=request.data.get("latitude"),
            longitude=request.data.get("longitude"),
            location_name=request.data.get("location_name", ""),
            unlock_radius_meters=request.data.get("unlock_radius_meters", 100),
            passphrase_hint=request.data.get("passphrase_hint", ""),
        )
        api_logger.info("capsule_created", extra={"action": "capsule_created", "user_id": str(request.user.id), "category": "capsules"})
        return Response(_serialize_capsule(capsule), status=status.HTTP_201_CREATED)


class CapsuleDetailView(APIView):
    """
    GET    /api/capsules/:id/  — get capsule (owner always; recipients only if unlocked)
    DELETE /api/capsules/:id/  — delete capsule (owner only; only while sealed)
    """
    permission_classes = [IsAuthenticated]

    def _get_capsule(self, capsule_id):
        try:
            return Capsule.objects.select_related("created_by", "encryption_key").prefetch_related("capsule_recipients", "contents").get(id=capsule_id)
        except Capsule.DoesNotExist:
            return None

    def get(self, request, capsule_id):
        capsule = self._get_capsule(capsule_id)
        if not capsule:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        if not capsule.is_accessible:
            return Response(
                {"error": "This capsule is broken and inaccessible"},
                status=status.HTTP_410_GONE,
            )

        is_owner = capsule.created_by_id == request.user.id
        is_recipient = capsule.capsule_recipients.filter(user=request.user).exists()

        if not is_owner and not is_recipient:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        if not is_owner and capsule.status != Capsule.Status.UNLOCKED:
            return Response(
                {"error": "This capsule is still sealed"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if is_recipient and capsule.status == Capsule.Status.UNLOCKED:
            capsule.capsule_recipients.filter(user=request.user, has_opened=False).update(
                has_opened=True, opened_at=timezone.now()
            )

        include_content = capsule.status == Capsule.Status.UNLOCKED
        return Response(_serialize_capsule(capsule, include_content=include_content, user=request.user))

    def delete(self, request, capsule_id):
        capsule = self._get_capsule(capsule_id)
        if not capsule:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        if capsule.created_by_id != request.user.id:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        if capsule.status != Capsule.Status.SEALED:
            return Response(
                {"error": "Only sealed capsules can be deleted"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        capsule.delete()
        api_logger.info("capsule_deleted", extra={"action": "capsule_deleted", "user_id": str(request.user.id), "category": "capsules"})
        return Response(status=status.HTTP_204_NO_CONTENT)


class CapsuleRecipientView(APIView):
    """
    POST /api/capsules/:id/recipients/  — add a recipient by user_id or email
    Owner only. Capsule must be sealed.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, capsule_id):
        try:
            capsule = Capsule.objects.get(id=capsule_id, created_by=request.user)
        except Capsule.DoesNotExist:
            return Response(
                {"error": "Not found or forbidden"}, status=status.HTTP_404_NOT_FOUND
            )

        if capsule.status != Capsule.Status.SEALED:
            return Response(
                {"error": "Cannot add recipients to an unlocked capsule"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Quota: capsule recipient limit ──
        sub = _get_sub(request.user)
        current_count = CapsuleRecipient.objects.filter(capsule=capsule).count()
        if current_count >= sub.max_recipients_per_capsule:
            return Response(
                {
                    "error": "Recipient limit reached",
                    "limit": sub.max_recipients_per_capsule,
                    "current": current_count,
                    "tier": sub.tier,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user_id = request.data.get("user_id")
        email = request.data.get("email", "").strip().lower()

        if not user_id and not email:
            return Response(
                {"error": "user_id or email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipient_user = None

        if user_id:
            try:
                recipient_user = FutrrUser.objects.get(id=user_id)
            except FutrrUser.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            _, created = CapsuleRecipient.objects.get_or_create(
                capsule=capsule,
                user=recipient_user,
                defaults={"added_via": CapsuleRecipient.AddedVia.INVITED},
            )
        else:
            created = False
            try:
                existing_user = FutrrUser.objects.get(email=email)
                recipient_user = existing_user
                _, created = CapsuleRecipient.objects.get_or_create(
                    capsule=capsule,
                    user=existing_user,
                    defaults={"added_via": CapsuleRecipient.AddedVia.INVITED},
                )
            except FutrrUser.DoesNotExist:
                CapsuleRecipient.objects.get_or_create(
                    capsule=capsule,
                    email=email,
                    defaults={"user": None, "added_via": CapsuleRecipient.AddedVia.INVITED},
                )

        # Notify the recipient if they're a registered user and were newly added
        if created and recipient_user:
            capsule_title = capsule.title or "Untitled capsule"
            sender_name = request.user.username
            Notification.objects.create(
                user=recipient_user,
                notif_type=Notification.NotifType.RECIPIENT_ADDED,
                title=f"You received an invitation for a capsule",
                body=f"@{sender_name} invited you to \"{capsule_title}\"",
                related_capsule=capsule,
            )

        return Response({"message": "Recipient added"}, status=status.HTTP_201_CREATED)


class CapsuleInvitationView(APIView):
    """
    POST   /api/capsules/:id/invitation/accept/  — accept; stays as recipient, marks notif read
    DELETE /api/capsules/:id/invitation/decline/ — decline; removes self from recipients
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, capsule_id):
        """Accept — just acknowledge; mark related notification(s) read."""
        Notification.objects.filter(
            user=request.user,
            notif_type=Notification.NotifType.RECIPIENT_ADDED,
            related_capsule_id=capsule_id,
            is_read=False,
        ).update(is_read=True)
        return Response({"accepted": True}, status=status.HTTP_200_OK)

    def delete(self, request, capsule_id):
        """Decline — remove self as recipient and mark notification read."""
        CapsuleRecipient.objects.filter(capsule_id=capsule_id, user=request.user).delete()
        Notification.objects.filter(
            user=request.user,
            notif_type=Notification.NotifType.RECIPIENT_ADDED,
            related_capsule_id=capsule_id,
        ).update(is_read=True)
        return Response({"declined": True}, status=status.HTTP_200_OK)


class CapsuleJoinView(APIView):
    """
    GET /api/capsules/join/:share_token/

    Auto-adds the authenticated user as a recipient via the share link.
    Public capsule  → added_via = PUBLIC
    Private capsule → added_via = LINK
    Content is only returned if the capsule is already UNLOCKED.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, share_token):
        try:
            capsule = Capsule.objects.get(share_token=share_token)
        except Capsule.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        if not capsule.is_accessible:
            return Response(
                {"error": "This capsule is broken and inaccessible"},
                status=status.HTTP_410_GONE,
            )

        added_via = (
            CapsuleRecipient.AddedVia.PUBLIC
            if capsule.is_public
            else CapsuleRecipient.AddedVia.LINK
        )
        CapsuleRecipient.objects.get_or_create(
            capsule=capsule,
            user=request.user,
            defaults={"added_via": added_via},
        )

        include_content = capsule.status == Capsule.Status.UNLOCKED
        return Response(_serialize_capsule(capsule, include_content=include_content, user=request.user))


# ---------------------------------------------------------------------------
# Capsule Unlock
# ---------------------------------------------------------------------------

class CapsuleUnlockView(APIView):
    """
    POST /api/capsules/:id/unlock/

    Attempts to permanently unlock a SEALED capsule.

    Rules:
    - The capsule's unlock_at time must have already passed.
    - Requester must be the owner or a named recipient.
    - For UMK (passphrase-protected) capsules a `passphrase` field is required
      in the request body; it is verified against the stored PBKDF2 key verifier.
    - For SMK / unencrypted capsules no passphrase is needed.

    On success the capsule status is persisted as UNLOCKED and the full capsule
    including decrypted contents is returned.  Subsequent calls for an already-
    UNLOCKED capsule are idempotent — they just return the contents again.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, capsule_id):
        try:
            capsule = Capsule.objects.select_related("created_by", "encryption_key").prefetch_related("capsule_recipients", "contents").get(id=capsule_id)
        except Capsule.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        if not capsule.is_accessible:
            return Response(
                {"error": "This capsule is broken and inaccessible"},
                status=status.HTTP_410_GONE,
            )

        is_owner = capsule.created_by_id == request.user.id
        is_recipient = capsule.capsule_recipients.filter(user=request.user).exists()

        if not is_owner and not is_recipient:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        # Idempotent: already unlocked — just return contents
        if capsule.status == Capsule.Status.UNLOCKED:
            if is_recipient:
                capsule.capsule_recipients.filter(
                    user=request.user, has_opened=False
                ).update(has_opened=True, opened_at=timezone.now())
            return Response(_serialize_capsule(capsule, include_content=True, user=request.user))

        if not capsule.is_ready_to_unlock:
            return Response(
                {"error": "This capsule cannot be opened yet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Verify passphrase for UMK capsules
        try:
            enc_key = capsule.encryption_key
            if enc_key.strategy == CapsuleEncryptionKey.KeyStrategy.UMK:
                passphrase = (request.data.get("passphrase") or "").strip()
                if not passphrase:
                    return Response(
                        {"error": "A passphrase is required to unlock this capsule"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not _verify_passphrase(passphrase, enc_key):
                    return Response(
                        {"error": "Invalid passphrase"},
                        status=status.HTTP_403_FORBIDDEN,
                    )
        except CapsuleEncryptionKey.DoesNotExist:
            pass  # No encryption key — no passphrase required

        # Permanently transition status to UNLOCKED and persist
        capsule.unlock()
        api_logger.info("capsule_unlocked", extra={"action": "capsule_unlocked", "user_id": str(request.user.id), "category": "capsules"})

        if is_recipient:
            capsule.capsule_recipients.filter(
                user=request.user, has_opened=False
            ).update(has_opened=True, opened_at=timezone.now())

        return Response(_serialize_capsule(capsule, include_content=True))


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

class EventListCreateView(APIView):
    """
    GET  /api/events/  — list public events (+ user's own)
    POST /api/events/  — create a new event
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Q
        qs = (
            Event.objects.filter(Q(is_public=True) | Q(created_by=request.user))
            .select_related("created_by")
            .order_by("-created_at")
        )
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(50, max(1, int(request.query_params.get("page_size", 20))))
        except (ValueError, TypeError):
            page, page_size = 1, 20

        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        events = list(qs[start:end])

        return Response({
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": [_serialize_event(e) for e in events],
        })

    def post(self, request):
        title = request.data.get("title", "").strip()
        is_time_locked = request.data.get("is_time_locked", True)
        unlock_at = request.data.get("unlock_at")

        if not title:
            return Response({"error": "title is required"}, status=status.HTTP_400_BAD_REQUEST)
        if is_time_locked and not unlock_at:
            return Response({"error": "unlock_at is required for time-locked events"}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = request.data.get("allowed_content_types", ["text", "photo", "video", "voice"])
        if not isinstance(allowed_types, list):
            allowed_types = ["text", "photo", "video", "voice"]

        # Validate slug uniqueness
        import re
        slug = request.data.get("slug", "").strip().lower()
        if slug:
            slug = re.sub(r"[^a-z0-9-]", "-", slug).strip("-")
            slug = re.sub(r"-+", "-", slug)
            if Event.objects.filter(slug=slug).exists():
                return Response({"error": "This URL slug is already taken"}, status=status.HTTP_400_BAD_REQUEST)

        # ── Quota: weekly event limit ──
        sub = _get_sub(request.user)
        events_this_week = Event.objects.filter(
            created_by=request.user, created_at__gte=_week_start()
        ).count()
        if events_this_week >= sub.max_events_per_week:
            return Response(
                {
                    "error": "Weekly event limit reached",
                    "limit": sub.max_events_per_week,
                    "current": events_this_week,
                    "tier": sub.tier,
                    "resets": "monday",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        event = Event.objects.create(
            title=title,
            subtitle=request.data.get("subtitle", ""),
            description=request.data.get("description", ""),
            slug=slug or None,
            created_by=request.user,
            unlock_at=unlock_at if is_time_locked else None,
            is_public=request.data.get("is_public", False),
            event_type=request.data.get("event_type", "other"),
            event_type_label=request.data.get("event_type_label", ""),
            is_time_locked=is_time_locked,
            entry_start=request.data.get("entry_start") or None,
            entry_close=request.data.get("entry_close") or None,
            max_participants=request.data.get("max_participants") or None,
            allowed_content_types=allowed_types,
        )

        banner_file = request.FILES.get("banner_image")
        if banner_file:
            ext = banner_file.name.rsplit(".", 1)[-1] if "." in banner_file.name else "jpg"
            s3_key = f"event_banners/{event.id}/banner.{ext}"
            upload_file(s3_key, banner_file, banner_file.content_type or "image/jpeg")
            event.banner_image = s3_key
            event.save(update_fields=["banner_image"])
            s3_logger.info("s3_upload", extra={"action": "s3_upload", "s3_key": s3_key, "user_id": str(request.user.id)})

        api_logger.info("event_created", extra={"action": "event_created", "user_id": str(request.user.id), "category": "events"})
        return Response(_serialize_event(event), status=status.HTTP_201_CREATED)


class EventDetailView(APIView):
    """
    GET   /api/events/:id/  — get event details
    PATCH /api/events/:id/  — update event (organizer only)
    DELETE /api/events/:id/ — delete event (organizer only); capsules are preserved via SET_NULL
    """
    permission_classes = [IsAuthenticated]

    def _get_event(self, event_id):
        try:
            return Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return None

    def get(self, request, event_id):
        event = self._get_event(event_id)
        if not event:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_serialize_event(event, user=request.user))

    def patch(self, request, event_id):
        event = self._get_event(event_id)
        if not event:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if event.created_by_id != request.user.id:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        updatable = [
            "title", "subtitle", "description", "event_type", "event_type_label",
            "is_time_locked", "unlock_at", "entry_start", "entry_close",
            "is_public", "max_participants", "allowed_content_types",
        ]
        for field in updatable:
            if field in request.data:
                setattr(event, field, request.data[field] if request.data[field] != "" else None)

        # Handle slug update
        if "slug" in request.data:
            import re
            slug = request.data["slug"].strip().lower() if request.data["slug"] else ""
            if slug:
                slug = re.sub(r"[^a-z0-9-]", "-", slug).strip("-")
                slug = re.sub(r"-+", "-", slug)
                if Event.objects.filter(slug=slug).exclude(id=event.id).exists():
                    return Response({"error": "This URL slug is already taken"}, status=status.HTTP_400_BAD_REQUEST)
                event.slug = slug
            else:
                event.slug = None

        # allowed_content_types must be a list
        if "allowed_content_types" in request.data:
            val = request.data["allowed_content_types"]
            event.allowed_content_types = val if isinstance(val, list) else ["text", "photo", "video", "voice"]

        # Validate: time-locked events must have unlock_at
        if event.is_time_locked and not event.unlock_at:
            return Response(
                {"error": "unlock_at is required for time-locked events"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event.save()

        banner_file = request.FILES.get("banner_image")
        if banner_file:
            ext = banner_file.name.rsplit(".", 1)[-1] if "." in banner_file.name else "jpg"
            s3_key = f"event_banners/{event.id}/banner.{ext}"
            upload_file(s3_key, banner_file, banner_file.content_type or "image/jpeg")
            event.banner_image = s3_key
            event.save(update_fields=["banner_image"])

        return Response(_serialize_event(event))

    def delete(self, request, event_id):
        event = self._get_event(event_id)
        if not event:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        if event.created_by_id != request.user.id:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        # Capsule.event FK has on_delete=SET_NULL — deleting the event automatically
        # nullifies capsule.event for all associated capsules without deleting them.
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EventSlugCheckView(APIView):
    """
    GET /api/events/check-slug/?slug=<slug>
    Returns { available: true/false }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import re
        slug = request.query_params.get("slug", "").strip().lower()
        if not slug:
            return Response({"available": False, "error": "slug is required"})
        slug = re.sub(r"[^a-z0-9-]", "-", slug).strip("-")
        slug = re.sub(r"-+", "-", slug)
        exists = Event.objects.filter(slug=slug).exists()
        return Response({"available": not exists, "slug": slug})


class EventJoinView(APIView):
    """
    POST /api/events/join/:invite_token/

    Join an event and seal a personal capsule inside it.
    The event's unlock_at is authoritative — the capsule's unlock_at is forced
    to match regardless of what the client sends.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, invite_token):
        try:
            event = Event.objects.get(invite_token=invite_token)
        except Event.DoesNotExist:
            return Response({"error": "Invalid invite token"}, status=status.HTTP_404_NOT_FOUND)

        if Capsule.objects.filter(event=event, created_by=request.user).exists():
            return Response(
                {"error": "You already have a capsule in this event"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Quota: event participant limit (checked against organiser's subscription) ──
        organiser = event.created_by
        if organiser:
            sub = _get_sub(organiser)
            participant_count = Capsule.objects.filter(event=event).count()
            if participant_count >= sub.max_event_participants:
                return Response(
                    {
                        "error": "This event has reached its participant limit",
                        "limit": sub.max_event_participants,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        capsule = Capsule.objects.create(
            title=request.data.get("title", ""),
            description=request.data.get("description", ""),
            created_by=request.user,
            event=event,
            unlock_at=event.unlock_at,  # event controls unlock time — not the client
        )
        return Response(_serialize_capsule(capsule), status=status.HTTP_201_CREATED)


class EventCapsulesView(APIView):
    """
    GET /api/events/:id/capsules/

    List all capsules in an event. Content is always hidden until unlock.
    After unlock, each user sees only their own capsule's content.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        event_capsules = list(event.capsules.all().select_related("created_by"))
        fav_ids = set(
            CapsuleFavorite.objects.filter(
                user=request.user, capsule_id__in=[c.id for c in event_capsules]
            ).values_list("capsule_id", flat=True)
        )
        result = []
        for capsule in event_capsules:
            own = capsule.created_by_id == request.user.id
            unlocked = capsule.status == Capsule.Status.UNLOCKED
            result.append(_serialize_capsule(
                capsule, include_content=(own and unlocked),
                user=request.user, favorited_ids=fav_ids,
            ))

        return Response(result)


# ---------------------------------------------------------------------------
# Capsule Content Upload
# ---------------------------------------------------------------------------

class CapsuleContentView(APIView):
    """
    POST /api/capsules/:id/contents/

    Add a piece of content (text, photo, voice, video) to a sealed capsule.
    Owner only.

    Text:  JSON body  { "content_type": "text", "body": "..." }
    Media: multipart  content_type=photo|voice|video  +  file=<binary>
                      optional: duration (seconds, for voice/video)
    """
    permission_classes = [IsAuthenticated]

    _S3_CONTENT_TYPES = {
        CapsuleContent.ContentType.PHOTO: "image/jpeg",
        CapsuleContent.ContentType.VOICE: "audio/mpeg",
        CapsuleContent.ContentType.VIDEO: "video/mp4",
    }

    def post(self, request, capsule_id):
        try:
            capsule = Capsule.objects.get(id=capsule_id, created_by=request.user)
        except Capsule.DoesNotExist:
            return Response(
                {"error": "Not found or forbidden"}, status=status.HTTP_404_NOT_FOUND
            )

        if capsule.status != Capsule.Status.SEALED:
            return Response(
                {"error": "Content can only be added to a sealed capsule"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_type = request.data.get("content_type", "").lower()
        valid_types = [c.value for c in CapsuleContent.ContentType]
        if raw_type not in valid_types:
            return Response(
                {"error": f"content_type must be one of: {', '.join(valid_types)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if raw_type == CapsuleContent.ContentType.TEXT:
            body = request.data.get("body", "").strip()
            if not body:
                return Response(
                    {"error": "body is required for text content"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            content = CapsuleContent.objects.create(
                capsule=capsule,
                added_by=request.user,
                content_type=raw_type,
                body=body,
            )
        else:
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                return Response(
                    {"error": "file is required for media content"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            content_id = uuid.uuid4()
            ext = uploaded_file.name.rsplit(".", 1)[-1] if "." in uploaded_file.name else "bin"
            s3_key = f"capsule_media/{capsule.id}/{raw_type}_{content_id}.{ext}"

            mime = self._S3_CONTENT_TYPES.get(raw_type, "application/octet-stream")
            file_size = uploaded_file.size
            upload_encrypted_media(s3_key, uploaded_file, mime)
            s3_logger.info("s3_upload", extra={"action": "s3_upload", "s3_key": s3_key, "user_id": str(request.user.id)})

            content = CapsuleContent.objects.create(
                capsule=capsule,
                added_by=request.user,
                content_type=raw_type,
                file=s3_key,
                file_size=file_size,
                duration=request.data.get("duration"),
            )

        return Response(
            {
                "id": str(content.id),
                "content_type": content.content_type,
                "created_at": content.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Discover (public capsules feed)
# ---------------------------------------------------------------------------

class DiscoverView(APIView):
    """
    GET /api/discover/

    Paginated feed of public capsules.
    Query params:
      status  — filter by capsule status (default: all non-broken)
      page    — page number (default: 1)
      page_size — results per page (default: 20, max: 50)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Capsule.objects.filter(is_public=True).exclude(
            status=Capsule.Status.BROKEN
        ).order_by("-created_at")

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(50, max(1, int(request.query_params.get("page_size", 20))))
        except (ValueError, TypeError):
            page, page_size = 1, 20

        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        capsules = list(qs.select_related("created_by", "encryption_key").prefetch_related("capsule_recipients")[start:end])
        fav_ids = set(
            CapsuleFavorite.objects.filter(
                user=request.user, capsule_id__in=[c.id for c in capsules]
            ).values_list("capsule_id", flat=True)
        )

        return Response(
            {
                "total": total,
                "page": page,
                "page_size": page_size,
                "results": [_serialize_capsule(c, user=request.user, favorited_ids=fav_ids) for c in capsules],
            }
        )


# ---------------------------------------------------------------------------
# Map / Atlas (location-tagged public capsules)
# ---------------------------------------------------------------------------

class CapsuleMapView(APIView):
    """
    GET /api/capsules/map/

    Returns public, location-tagged capsules for the Atlas map view.
    Filter by bounding box:
      lat_min, lat_max, lng_min, lng_max  — required
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            lat_min = float(request.query_params["lat_min"])
            lat_max = float(request.query_params["lat_max"])
            lng_min = float(request.query_params["lng_min"])
            lng_max = float(request.query_params["lng_max"])
        except (KeyError, ValueError, TypeError):
            return Response(
                {"error": "lat_min, lat_max, lng_min, lng_max are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        capsules = list(Capsule.objects.filter(
            is_public=True,
            listed_in_atlas=True,
            latitude__isnull=False,
            longitude__isnull=False,
            latitude__gte=lat_min,
            latitude__lte=lat_max,
            longitude__gte=lng_min,
            longitude__lte=lng_max,
        ).exclude(status=Capsule.Status.BROKEN).select_related("created_by", "encryption_key").prefetch_related("capsule_recipients"))
        fav_ids = set(
            CapsuleFavorite.objects.filter(
                user=request.user, capsule_id__in=[c.id for c in capsules]
            ).values_list("capsule_id", flat=True)
        )

        return Response([_serialize_capsule(c, user=request.user, favorited_ids=fav_ids) for c in capsules])


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------

class CapsuleFavoriteView(APIView):
    """
    POST /api/capsules/:id/favorite/

    Toggle favorite on a capsule. Returns the new state.
    Capsule must be accessible (not broken).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, capsule_id):
        try:
            capsule = Capsule.objects.get(id=capsule_id)
        except Capsule.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        if not capsule.is_accessible:
            return Response(
                {"error": "This capsule is broken and inaccessible"},
                status=status.HTTP_410_GONE,
            )

        favorite, created = CapsuleFavorite.objects.get_or_create(
            user=request.user, capsule=capsule
        )
        if not created:
            favorite.delete()
            return Response({"favorited": False})

        return Response({"favorited": True}, status=status.HTTP_201_CREATED)


class CapsuleFavoritesListView(APIView):
    """
    GET /api/capsules/favorites/
    List all capsules the requesting user has favorited.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        capsules = list(
            Capsule.objects.filter(
                favorited_by__user=request.user
            ).exclude(status=Capsule.Status.BROKEN)
            .select_related("created_by", "encryption_key")
            .prefetch_related("capsule_recipients", "contents")
            .order_by("-favorited_by__created_at")
        )
        fav_ids = {c.id for c in capsules}  # all are favorited
        return Response([
            _serialize_capsule(c, include_content=(c.status == Capsule.Status.UNLOCKED),
                               user=request.user, favorited_ids=fav_ids)
            for c in capsules
        ])


# ---------------------------------------------------------------------------
# Discover Search
# ---------------------------------------------------------------------------

class DiscoverSearchView(APIView):
    """
    GET /api/discover/search/?q=<query>

    Unified search returning:
      capsules  — public capsules whose title/description matches
      people    — users whose username matches
      events    — events whose title matches
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Count
        from users.models import FutrrUser, Follow
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"capsules": [], "people": [], "events": []})

        capsules = list(
            Capsule.objects.filter(
                is_public=True,
                title__icontains=q,
            ).exclude(status=Capsule.Status.BROKEN)
            .select_related("created_by", "encryption_key")
            .prefetch_related("capsule_recipients")[:20]
        )
        fav_ids = set(
            CapsuleFavorite.objects.filter(
                user=request.user, capsule_id__in=[c.id for c in capsules]
            ).values_list("capsule_id", flat=True)
        )

        people = list(
            FutrrUser.objects.filter(username__icontains=q)
            .exclude(id=request.user.id)
            .annotate(
                followers_count_ann=Count("followers", distinct=True),
                following_count_ann=Count("following", distinct=True),
            )[:20]
        )
        following_ids = set(
            Follow.objects.filter(
                follower=request.user, following_id__in=[u.id for u in people]
            ).values_list("following_id", flat=True)
        )

        events = Event.objects.filter(title__icontains=q)[:20]

        from users.api import _serialize_user
        return Response({
            "capsules": [_serialize_capsule(c, user=request.user, favorited_ids=fav_ids) for c in capsules],
            "people": [_serialize_user(u, request.user, following_ids=following_ids) for u in people],
            "events": [_serialize_event(e) for e in events],
        })


class FriendsFeedView(APIView):
    """
    GET /api/discover/friends/
    Capsules created by users the requesting user follows.
    Public capsules only.
    Query params: page (default 1), page_size (default 20, max 50)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from users.models import Follow
        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list("following_id", flat=True)

        qs = (
            Capsule.objects.filter(
                created_by_id__in=following_ids,
                is_public=True,
            ).exclude(status=Capsule.Status.BROKEN)
            .select_related("created_by", "encryption_key")
            .prefetch_related("capsule_recipients")
            .order_by("-created_at")
        )

        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(50, max(1, int(request.query_params.get("page_size", 20))))
        except (ValueError, TypeError):
            page, page_size = 1, 20

        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        capsules = list(qs[start:end])
        fav_ids = set(
            CapsuleFavorite.objects.filter(
                user=request.user, capsule_id__in=[c.id for c in capsules]
            ).values_list("capsule_id", flat=True)
        )
        return Response({
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": [_serialize_capsule(c, user=request.user, favorited_ids=fav_ids) for c in capsules],
        })


class GlobalFeedView(APIView):
    """
    GET /api/discover/global/
    Global public events and capsules ordered by newest.
    Query params: page (default 1), page_size (default 20, max 50)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(50, max(1, int(request.query_params.get("page_size", 20))))
        except (ValueError, TypeError):
            page, page_size = 1, 20

        start = (page - 1) * page_size
        end = start + page_size

        events_qs = Event.objects.filter(is_public=True).select_related("created_by").order_by("-created_at")
        capsules_qs = (
            Capsule.objects.filter(is_public=True)
            .exclude(status=Capsule.Status.BROKEN)
            .select_related("created_by", "encryption_key")
            .prefetch_related("capsule_recipients")
            .order_by("-created_at")
        )

        total_events = events_qs.count()
        total_capsules = capsules_qs.count()
        events = list(events_qs[start:end])
        capsules = list(capsules_qs[start:end])

        fav_ids = set(
            CapsuleFavorite.objects.filter(
                user=request.user, capsule_id__in=[c.id for c in capsules]
            ).values_list("capsule_id", flat=True)
        )
        return Response({
            "total_events": total_events,
            "total_capsules": total_capsules,
            "page": page,
            "page_size": page_size,
            "events": [_serialize_event(e) for e in events],
            "capsules": [_serialize_capsule(c, user=request.user, favorited_ids=fav_ids) for c in capsules],
        })


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def _serialize_notification(notif):
    return {
        "id": str(notif.id),
        "type": notif.notif_type,
        "title": notif.title,
        "body": notif.body,
        "is_read": notif.is_read,
        "related_capsule": str(notif.related_capsule_id) if notif.related_capsule_id else None,
        "related_capsule_title": notif.related_capsule.title if notif.related_capsule_id and hasattr(notif, "related_capsule") and notif.related_capsule else None,
        "related_event": str(notif.related_event_id) if notif.related_event_id else None,
        "created_at": notif.created_at,
    }


class NotificationListView(APIView):
    """
    GET  /api/notifications/         — list notifications (latest first)
    Query params:
      unread_only=true               — only unread notifications
      page                           — page number (default: 1)
      page_size                      — results per page (default: 20, max: 50)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(user=request.user)
        if request.query_params.get("unread_only", "").lower() == "true":
            qs = qs.filter(is_read=False)

        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(50, max(1, int(request.query_params.get("page_size", 20))))
        except (ValueError, TypeError):
            page, page_size = 1, 20

        start = (page - 1) * page_size
        end = start + page_size
        total = qs.count()
        notifications = list(qs.select_related("related_capsule")[start:end])
        return Response({
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": [_serialize_notification(n) for n in notifications],
        })


class NotificationReadView(APIView):
    """
    PATCH/POST /api/notifications/:id/read/  — mark a notification as read
    """
    permission_classes = [IsAuthenticated]

    def _mark_read(self, request, notif_id):
        try:
            notif = Notification.objects.get(id=notif_id, user=request.user)
        except Notification.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return Response({"message": "Marked as read"})

    def patch(self, request, notif_id):
        return self._mark_read(request, notif_id)

    def post(self, request, notif_id):
        return self._mark_read(request, notif_id)


# ---------------------------------------------------------------------------
# Capsule Pin
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Capsule Visibility
# ---------------------------------------------------------------------------

class CapsuleVisibilityView(APIView):
    """
    PATCH /api/capsules/:id/visibility/

    Update capsule visibility settings.  Owner only.
    Body (all optional):
      is_public: bool            — make public or private
      listed_in_atlas: bool      — list/unlist from the Atlas map
      latitude: float            — atlas pin location
      longitude: float           — atlas pin location
      location_name: string      — human-readable location label

    When listed_in_atlas is set to True, the capsule is also made public.
    When a public capsule is made private:
      - All pins are deleted (auto-unpin from every profile)
      - listed_in_atlas is reset to False
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, capsule_id):
        try:
            capsule = Capsule.objects.get(id=capsule_id)
        except Capsule.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        if capsule.created_by != request.user:
            return Response(
                {"error": "Only the capsule owner can change visibility"},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_public = request.data.get("is_public")
        new_atlas = request.data.get("listed_in_atlas")
        updated = []

        # Show in Atlas implicitly makes the capsule public
        if new_atlas and not capsule.is_public:
            capsule.is_public = True
            updated.append("is_public")

        if new_public is not None:
            capsule.is_public = new_public
            updated.append("is_public") if "is_public" not in updated else None

            # Public → Private: remove from atlas
            if not new_public:
                capsule.listed_in_atlas = False
                updated.append("listed_in_atlas")

        if new_atlas is not None and capsule.is_public:
            capsule.listed_in_atlas = new_atlas
            if "listed_in_atlas" not in updated:
                updated.append("listed_in_atlas")

        # Update location when listing on atlas
        lat = request.data.get("latitude")
        lng = request.data.get("longitude")
        loc_name = request.data.get("location_name")
        if lat is not None and lng is not None:
            capsule.latitude = lat
            capsule.longitude = lng
            updated.extend(f for f in ["latitude", "longitude"] if f not in updated)
        if loc_name is not None:
            capsule.location_name = loc_name
            if "location_name" not in updated:
                updated.append("location_name")

        if updated:
            capsule.save(update_fields=updated)

        return Response({
            "is_public": capsule.is_public,
            "listed_in_atlas": capsule.listed_in_atlas,
            "latitude": capsule.latitude,
            "longitude": capsule.longitude,
            "location_name": capsule.location_name,
        })



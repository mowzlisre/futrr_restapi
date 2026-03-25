from django.db.models.signals import pre_delete
from django.dispatch import receiver
from users.models import FutrrUser
from .models import Capsule, CapsuleContent, CapsuleRecipient
from .s3 import delete_files


@receiver(pre_delete, sender=FutrrUser)
def handle_creator_deletion(sender, instance, **kwargs):
    """
    When a user deletes their account:
    1. Collect and delete all S3 media from their capsules (best-effort).
    2. Delete the avatar S3 file if applicable.
    3. Permanently delete all capsules they created (cascades to CapsuleContent).
    """
    # Collect all S3 keys from capsule contents
    s3_keys = list(
        CapsuleContent.objects.filter(capsule__created_by=instance)
        .exclude(file__isnull=True)
        .exclude(file="")
        .values_list("file", flat=True)
    )

    # Include avatar if it's an S3 key
    if instance.avatar and instance.avatar.startswith("user_avatars/"):
        s3_keys.append(instance.avatar)

    # Delete from S3 best-effort (don't let S3 errors block account deletion)
    if s3_keys:
        try:
            delete_files(s3_keys)
        except Exception:
            pass

    # Permanently delete all capsules (cascades to CapsuleContent rows)
    instance.capsules_created.all().delete()


@receiver(pre_delete, sender=FutrrUser)
def handle_recipient_deletion(sender, instance, **kwargs):
    """
    When a user deletes their account, remove them as a recipient from all
    capsules. The capsules themselves are unaffected.
    """
    CapsuleRecipient.objects.filter(user=instance).delete()

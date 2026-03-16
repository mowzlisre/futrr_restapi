from django.db.models.signals import pre_delete
from django.dispatch import receiver
from users.models import FutrrUser
from .models import Capsule, CapsuleRecipient


@receiver(pre_delete, sender=FutrrUser)
def handle_creator_deletion(sender, instance, **kwargs):
    """
    When a user deletes their account, all capsules they created are permanently
    marked BROKEN and created_by is nulled. A broken capsule can never be
    unlocked or accessed — by anyone, including the system.
    """
    instance.capsules_created.update(
        status=Capsule.Status.BROKEN,
        created_by=None,
    )


@receiver(pre_delete, sender=FutrrUser)
def handle_recipient_deletion(sender, instance, **kwargs):
    """
    When a user deletes their account, remove them as a recipient from all
    capsules. The capsules themselves are unaffected.
    """
    CapsuleRecipient.objects.filter(user=instance).delete()

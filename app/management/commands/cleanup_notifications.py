from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app.models import Notification


class Command(BaseCommand):
    help = "Delete notifications older than 7 days."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=7)
        deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
        self.stdout.write(f"Deleted {deleted} notifications older than 7 days.")

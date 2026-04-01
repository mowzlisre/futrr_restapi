from django.core.management.base import BaseCommand
from users.emails import send_welcome_email


class Command(BaseCommand):
    help = "Send a test welcome email via AWS SES"

    def handle(self, *args, **options):
        recipient = "speak2mowzli@gmail.com"
        self.stdout.write(f"Sending test welcome email to {recipient} ...")

        try:
            send_welcome_email(recipient, "mowzli")
            self.stdout.write(self.style.SUCCESS(f"Welcome email sent to {recipient}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed: {e}"))

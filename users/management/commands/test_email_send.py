"""
Quick diagnostic: test sending email via 3 different methods from inside the container.
Usage: python manage.py test_email_send speak2mowzli@gmail.com
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Test email sending via boto3 and django to diagnose SES issues"

    def add_arguments(self, parser):
        parser.add_argument("recipient", type=str)

    def handle(self, recipient, **options):
        # Test 1: boto3 SES directly (same as CLI)
        self.stdout.write("\n=== Test 1: boto3 ses.send_email ===")
        try:
            import boto3
            client = boto3.client("ses", region_name="us-east-1")
            resp = client.send_email(
                Source="Futrr <no-reply@futrr.app>",
                Destination={"ToAddresses": [recipient]},
                Message={
                    "Subject": {"Data": "Test 1 - boto3 direct"},
                    "Body": {"Text": {"Data": "Sent via boto3 ses.send_email"}},
                },
            )
            self.stdout.write(self.style.SUCCESS(f"OK: {resp['MessageId']}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"FAILED: {e}"))

        # Test 2: boto3 send_raw_email (what django-ses uses)
        self.stdout.write("\n=== Test 2: boto3 ses.send_raw_email ===")
        try:
            import boto3
            from email.mime.text import MIMEText
            client = boto3.client("ses", region_name="us-east-1")
            msg = MIMEText("Sent via boto3 send_raw_email")
            msg["Subject"] = "Test 2 - boto3 raw"
            msg["From"] = "Futrr <no-reply@futrr.app>"
            msg["To"] = recipient
            resp = client.send_raw_email(
                Source="Futrr <no-reply@futrr.app>",
                Destinations=[recipient],
                RawMessage={"Data": msg.as_string()},
            )
            self.stdout.write(self.style.SUCCESS(f"OK: {resp['MessageId']}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"FAILED: {e}"))

        # Test 3: Django email (uses django-ses backend)
        self.stdout.write("\n=== Test 3: Django send_mail ===")
        try:
            from django.core.mail import send_mail
            send_mail(
                "Test 3 - Django send_mail",
                "Sent via Django email backend (django-ses)",
                "Futrr <no-reply@futrr.app>",
                [recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"FAILED: {e}"))

        # Print credentials info
        self.stdout.write("\n=== Credential Info ===")
        try:
            import boto3
            sts = boto3.client("sts", region_name="us-east-1")
            identity = sts.get_caller_identity()
            self.stdout.write(f"Account: {identity['Account']}")
            self.stdout.write(f"ARN: {identity['Arn']}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"STS FAILED: {e}"))

        # Print django-ses config
        self.stdout.write("\n=== Django-SES Config ===")
        from django.conf import settings
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"AWS_SES_REGION_NAME: {getattr(settings, 'AWS_SES_REGION_NAME', 'NOT SET')}")
        self.stdout.write(f"AWS_SES_REGION_ENDPOINT: {getattr(settings, 'AWS_SES_REGION_ENDPOINT', 'NOT SET')}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"AWS_SES_ACCESS_KEY_ID: {'SET' if getattr(settings, 'AWS_SES_ACCESS_KEY_ID', None) else 'NOT SET (using default chain)'}")

import os
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings

ICON_DIR = os.path.join(settings.BASE_DIR, "static", "email-icons")

ASSETS = [
    {"local": os.path.join(ICON_DIR, "icon-capsule.png"), "key": "email-assets/icon-capsule.png", "content_type": "image/png"},
    {"local": os.path.join(ICON_DIR, "icon-globe.png"), "key": "email-assets/icon-globe.png", "content_type": "image/png"},
    {"local": os.path.join(ICON_DIR, "icon-timeline.png"), "key": "email-assets/icon-timeline.png", "content_type": "image/png"},
]

S3_BUCKET = "futrr"


class Command(BaseCommand):
    help = "Upload email icon assets to the futrr S3 bucket"

    def handle(self, *args, **options):
        client = boto3.client("s3", region_name=settings.AWS_REGION)

        for asset in ASSETS:
            path = os.path.normpath(asset["local"])
            if not os.path.exists(path):
                self.stdout.write(self.style.ERROR(f"Not found: {path}"))
                continue

            client.upload_file(
                path,
                S3_BUCKET,
                asset["key"],
                ExtraArgs={
                    "ContentType": asset["content_type"],
                    "CacheControl": "public, max-age=31536000",
                },
            )
            url = f"https://{S3_BUCKET}.s3.us-east-1.amazonaws.com/{asset['key']}"
            self.stdout.write(self.style.SUCCESS(f"Uploaded: {url}"))

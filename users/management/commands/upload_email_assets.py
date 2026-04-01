import os
import json
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings

ASSETS = [
    {
        "local": os.path.join(settings.BASE_DIR, "..", "futrr-mobile", "assets", "futrr-banner-transparent.png"),
        "key": "email-assets/futrr-banner.png",
        "content_type": "image/png",
    },
]


class Command(BaseCommand):
    help = "Upload email assets to S3 and set public read policy for email-assets/"

    def handle(self, *args, **options):
        client = boto3.client("s3", region_name=settings.AWS_REGION)
        bucket = settings.AWS_S3_BUCKET

        for asset in ASSETS:
            path = os.path.normpath(asset["local"])
            if not os.path.exists(path):
                self.stdout.write(self.style.ERROR(f"Not found: {path}"))
                continue

            client.upload_file(
                path,
                bucket,
                asset["key"],
                ExtraArgs={
                    "ContentType": asset["content_type"],
                    "CacheControl": "public, max-age=31536000",
                },
            )
            url = f"https://{bucket}.s3.amazonaws.com/{asset['key']}"
            self.stdout.write(self.style.SUCCESS(f"Uploaded: {url}"))

        # Add bucket policy to allow public read on email-assets/ prefix
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadEmailAssets",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket}/email-assets/*",
                }
            ],
        }

        try:
            # Merge with existing policy if one exists
            existing = client.get_bucket_policy(Bucket=bucket)
            existing_policy = json.loads(existing["Policy"])
            # Remove old email-assets statement if present
            existing_policy["Statement"] = [
                s for s in existing_policy["Statement"]
                if s.get("Sid") != "PublicReadEmailAssets"
            ]
            existing_policy["Statement"].append(policy["Statement"][0])
            policy = existing_policy
        except client.exceptions.from_code("NoSuchBucketPolicy"):
            pass
        except Exception:
            pass

        client.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
        self.stdout.write(self.style.SUCCESS("Bucket policy updated — email-assets/ is now public"))

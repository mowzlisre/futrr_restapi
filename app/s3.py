import boto3
from django.conf import settings

_s3 = None


def _get_client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3", region_name=settings.AWS_REGION)
    return _s3


def generate_presigned_url(s3_key: str, expiry_seconds: int = 900) -> str:
    """
    Generate a pre-signed GET URL for a capsule media file.

    IMPORTANT: Only call this after confirming the capsule is UNLOCKED.
    Never generate a pre-signed URL for a sealed or broken capsule.

    expiry_seconds default = 15 minutes (900s).
    """
    client = _get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_S3_BUCKET,
            "Key": s3_key,
        },
        ExpiresIn=expiry_seconds,
    )


def upload_encrypted_media(s3_key: str, encrypted_bytes: bytes, content_type: str) -> None:
    """
    Upload encrypted ciphertext to S3.

    content_type is metadata only — the actual bytes stored are ciphertext,
    not a readable media file.
    """
    client = _get_client()
    client.put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=s3_key,
        Body=encrypted_bytes,
        ContentType=content_type,
        ServerSideEncryption="AES256",
    )

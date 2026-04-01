import logging

import boto3
from django.conf import settings

logger = logging.getLogger("futrr.s3")

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


def upload_file(s3_key: str, file_obj, content_type: str) -> None:
    """
    Stream-upload a plain (non-encrypted) file to S3.
    Use this for user-facing assets such as avatars.
    """
    client = _get_client()
    try:
        client.upload_fileobj(
            file_obj,
            settings.AWS_S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": content_type},
        )
        logger.info("upload_success", extra={"action": "upload_success", "s3_key": s3_key})
    except Exception:
        logger.error("upload_failed", extra={"action": "upload_failed", "s3_key": s3_key}, exc_info=True)
        raise


def delete_file(s3_key: str) -> None:
    """Delete a single object from S3."""
    client = _get_client()
    try:
        client.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=s3_key)
        logger.info("delete_success", extra={"action": "delete_success", "s3_key": s3_key})
    except Exception:
        logger.error("delete_failed", extra={"action": "delete_failed", "s3_key": s3_key}, exc_info=True)
        raise


def delete_files(s3_keys: list) -> None:
    """
    Bulk-delete up to 1000 S3 objects in one request.
    Silently ignores keys that don't exist.
    """
    if not s3_keys:
        return
    client = _get_client()
    try:
        client.delete_objects(
            Bucket=settings.AWS_S3_BUCKET,
            Delete={
                "Objects": [{"Key": k} for k in s3_keys],
                "Quiet": True,
            },
        )
        logger.info("bulk_delete_success", extra={"action": "bulk_delete_success", "count": len(s3_keys)})
    except Exception:
        logger.error("bulk_delete_failed", extra={"action": "bulk_delete_failed", "count": len(s3_keys)}, exc_info=True)
        raise


def upload_encrypted_media(s3_key: str, file_obj, content_type: str) -> None:
    """
    Stream-upload encrypted ciphertext to S3.

    file_obj can be any file-like object (e.g. Django's InMemoryUploadedFile or
    TemporaryUploadedFile).  Uses upload_fileobj so the file is streamed in
    chunks rather than read entirely into memory first.

    content_type is metadata only — the actual bytes stored are ciphertext,
    not a readable media file.
    """
    client = _get_client()
    try:
        client.upload_fileobj(
            file_obj,
            settings.AWS_S3_BUCKET,
            s3_key,
            ExtraArgs={
                "ContentType": content_type,
                "ServerSideEncryption": "AES256",
            },
        )
        logger.info("encrypted_upload_success", extra={"action": "encrypted_upload_success", "s3_key": s3_key})
    except Exception:
        logger.error("encrypted_upload_failed", extra={"action": "encrypted_upload_failed", "s3_key": s3_key}, exc_info=True)
        raise

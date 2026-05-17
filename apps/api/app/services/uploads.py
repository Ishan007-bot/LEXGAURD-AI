"""Create resumable / V4-signed PUT URLs for direct browser uploads to GCS."""

from __future__ import annotations

import uuid
from datetime import timedelta

from app.clients.gcp import get_storage_client
from app.config import get_settings
from app.exceptions import UpstreamError, ValidationError
from app.schemas.upload import (
    ALLOWED_MIME_TYPES,
    MAX_UPLOAD_BYTES,
    UploadInitRequest,
    UploadInitResponse,
)

SIGNED_URL_TTL = timedelta(minutes=15)


def _validate_request(req: UploadInitRequest) -> None:
    if req.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"Unsupported content type: {req.content_type!r}",
            details={"allowed": sorted(ALLOWED_MIME_TYPES)},
        )
    if req.size_bytes > MAX_UPLOAD_BYTES:
        raise ValidationError(
            "File exceeds the maximum upload size.",
            details={"max_bytes": MAX_UPLOAD_BYTES},
        )


def init_upload(req: UploadInitRequest, user_id: str) -> UploadInitResponse:
    """Allocate a document id and return a one-shot signed PUT URL."""
    _validate_request(req)
    settings = get_settings()

    document_id = uuid.uuid4().hex
    object_path = f"users/{user_id}/documents/{document_id}/{req.filename}"

    try:
        bucket = get_storage_client().bucket(settings.gcs_upload_bucket)
        blob = bucket.blob(object_path)
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=SIGNED_URL_TTL,
            method="PUT",
            content_type=req.content_type,
        )
    except Exception as exc:  # noqa: BLE001 — surface any GCS failure uniformly
        raise UpstreamError("Could not create upload URL.") from exc

    return UploadInitResponse(
        document_id=document_id,
        upload_url=signed_url,
        headers={"Content-Type": req.content_type},
        expires_in_seconds=int(SIGNED_URL_TTL.total_seconds()),
        gcs_object=object_path,
    )

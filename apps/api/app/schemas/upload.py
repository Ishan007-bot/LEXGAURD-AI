"""Upload-related request/response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Keep this set tight: anything else gets rejected before we hit GCS.
ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
    }
)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MiB


class UploadInitRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    size_bytes: int = Field(gt=0, le=MAX_UPLOAD_BYTES)


class UploadInitResponse(BaseModel):
    document_id: str
    upload_url: str
    method: Literal["PUT"] = "PUT"
    headers: dict[str, str]
    expires_in_seconds: int
    gcs_object: str

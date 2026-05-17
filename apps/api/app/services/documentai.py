"""Document AI wrapper.

Reads a binary file from GCS and runs it through a Document AI processor to
get back plain text. For plain-text uploads (mime = `text/plain`) we skip
Document AI entirely to save the per-page cost.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.clients.gcp import get_storage_client
from app.config import get_settings
from app.exceptions import UpstreamError, ValidationError
from app.logging_setup import get_logger

if TYPE_CHECKING:  # pragma: no cover
    pass

logger = get_logger(__name__)

# MIME types we can hand to Document AI directly.
DOCAI_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }
)


def _read_gcs_object(bucket_name: str, object_path: str) -> bytes:
    try:
        bucket = get_storage_client().bucket(bucket_name)
        blob = bucket.blob(object_path)
        return blob.download_as_bytes()
    except Exception as exc:  # noqa: BLE001
        raise UpstreamError("Failed to read uploaded file from Cloud Storage.") from exc


def _extract_with_documentai(content: bytes, mime_type: str) -> str:
    """Call Document AI synchronously and return the recognized text."""
    settings = get_settings()
    if not settings.docai_processor_id:
        raise UpstreamError(
            "Document AI processor is not configured. Set DOCAI_PROCESSOR_ID in env."
        )

    # Lazy imports — keeps tests light and unit-friendly.
    from google.cloud import documentai

    client = documentai.DocumentProcessorServiceClient(
        client_options={"api_endpoint": f"{settings.docai_location}-documentai.googleapis.com"}
    )
    name = (
        f"projects/{settings.gcp_project_id}"
        f"/locations/{settings.docai_location}"
        f"/processors/{settings.docai_processor_id}"
    )

    request = documentai.ProcessRequest(
        name=name,
        raw_document=documentai.RawDocument(content=content, mime_type=mime_type),
    )
    try:
        response = client.process_document(request=request)
    except Exception as exc:  # noqa: BLE001
        logger.exception("documentai.process_failed", error=str(exc))
        raise UpstreamError("Document AI processing failed.") from exc

    text = response.document.text or ""
    if not text.strip():
        raise UpstreamError("Document AI returned an empty document.")
    return text


def extract_text_from_gcs(*, gcs_object: str, content_type: str) -> str:
    """Top-level entrypoint used by the pipeline service.

    Returns plain UTF-8 text. Raises `UpstreamError` or `ValidationError`.
    """
    settings = get_settings()
    content = _read_gcs_object(settings.gcs_upload_bucket, gcs_object)

    if content_type == "text/plain":
        try:
            return content.decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 — defensive
            raise UpstreamError("Could not decode plain-text upload.") from exc

    if content_type not in DOCAI_MIME_TYPES:
        raise ValidationError(f"Unsupported content type for extraction: {content_type!r}")

    return _extract_with_documentai(content, mime_type=content_type)

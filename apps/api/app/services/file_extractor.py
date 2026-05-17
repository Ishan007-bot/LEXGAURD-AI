"""In-process PDF / DOCX / TXT text extraction.

This is the deploy-free alternative to Document AI: we accept the file as a
multipart upload, pull text out with `pypdf` / `python-docx` right in the
request handler, and hand the result to the existing pipeline.

Use Document AI when running on Cloud Run for higher-fidelity extraction;
this path is for local dev and the hackathon demo.
"""

from __future__ import annotations

import io

from app.exceptions import UpstreamError, ValidationError

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
DOC_MIME = "application/msword"
TXT_MIME = "text/plain"

ACCEPTED_MIME_TYPES: frozenset[str] = frozenset({PDF_MIME, DOCX_MIME, DOC_MIME, TXT_MIME})
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MiB


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001 — pypdf raises many specific types
        raise UpstreamError("Could not open the PDF file.") from exc

    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:  # noqa: BLE001 — corrupt pages should not 500 the whole upload
            text = ""
        if text.strip():
            pages.append(text)

    text = "\n\n".join(pages)
    if not text.strip():
        raise UpstreamError(
            "Could not extract text from this PDF (likely scanned/image-only)."
        )
    return text


def _extract_docx(data: bytes) -> str:
    # `python-docx` only supports modern .docx (Office Open XML), not legacy .doc.
    from docx import Document as DocxDocument

    try:
        document = DocxDocument(io.BytesIO(data))
    except Exception as exc:  # noqa: BLE001
        raise UpstreamError(
            "Could not open the DOCX file (legacy .doc is unsupported — re-save as .docx)."
        ) from exc

    parts: list[str] = [p.text for p in document.paragraphs if p.text and p.text.strip()]
    text = "\n\n".join(parts)
    if not text.strip():
        raise UpstreamError("DOCX file contains no readable paragraphs.")
    return text


def _extract_txt(data: bytes) -> str:
    try:
        return data.decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        raise UpstreamError("Could not decode plain-text upload.") from exc


def extract_text(*, content: bytes, content_type: str) -> str:
    """Return UTF-8 text extracted from an uploaded file blob."""
    if not content:
        raise ValidationError("Uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValidationError(
            f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MiB limit."
        )
    if content_type not in ACCEPTED_MIME_TYPES:
        raise ValidationError(
            f"Unsupported file type: {content_type!r}. Use PDF, DOCX, or plain text.",
        )

    if content_type == PDF_MIME:
        return _extract_pdf(content)
    if content_type in (DOCX_MIME, DOC_MIME):
        return _extract_docx(content)
    return _extract_txt(content)

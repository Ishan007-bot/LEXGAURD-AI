"""End-to-end document processing.

Each public function in this module returns a fully-persisted `Document`
(status = `ready` or `failed`) and has no HTTP concerns. Route handlers in
`app/routes/documents.py` are thin adapters over these.
"""

from __future__ import annotations

import uuid

from app.exceptions import LexGuardError
from app.logging_setup import get_logger
from app.models import (
    Document,
    DocumentSource,
    DocumentStatus,
    DocumentType,
)
from app.repositories.documents import (
    DocumentRepository,
    FirestoreDocumentRepository,
)
from app.services import categorizer, documentai, dlp, segmenter, url_ingest

logger = get_logger(__name__)


def _default_repo() -> DocumentRepository:
    return FirestoreDocumentRepository()


def _finalize(document: Document, text: str, *, repo: DocumentRepository) -> Document:
    """Apply DLP, segmentation, categorisation; persist; return."""
    document.status = DocumentStatus.PROCESSING
    document.raw_text = text
    repo.save(document)

    redacted = dlp.redact(text, use_cloud_dlp=False)
    clauses = segmenter.segment(redacted)
    clauses = categorizer.categorize_clauses(clauses)

    document.redacted_text = redacted
    document.clauses = clauses
    document.status = DocumentStatus.READY
    repo.save(document)

    logger.info(
        "document.processed",
        document_id=document.id,
        clause_count=len(clauses),
        source=document.source.value,
    )
    return document


def _fail(document: Document, reason: str, *, repo: DocumentRepository) -> Document:
    document.status = DocumentStatus.FAILED
    document.failure_reason = reason
    repo.save(document)
    return document


# ---------------------------------------------------------------------------
# Public entrypoints
# ---------------------------------------------------------------------------


def process_uploaded_document(
    *,
    document_id: str,
    user_id: str,
    gcs_object: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    repo: DocumentRepository | None = None,
) -> Document:
    repo = repo or _default_repo()
    document = Document(
        id=document_id,
        user_id=user_id,
        source=DocumentSource.UPLOAD,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        gcs_object=gcs_object,
    )
    try:
        text = documentai.extract_text_from_gcs(
            gcs_object=gcs_object,
            content_type=content_type,
        )
        return _finalize(document, text, repo=repo)
    except LexGuardError as exc:
        logger.warning("document.processing_failed", document_id=document_id, reason=exc.message)
        return _fail(document, exc.message, repo=repo)


def process_pasted_text(
    *,
    user_id: str,
    text: str,
    document_type: DocumentType = DocumentType.OTHER,
    title: str | None = None,
    repo: DocumentRepository | None = None,
) -> Document:
    repo = repo or _default_repo()
    document = Document(
        id=uuid.uuid4().hex,
        user_id=user_id,
        source=DocumentSource.PASTED_TEXT,
        document_type=document_type,
        filename=title,
    )
    try:
        return _finalize(document, text, repo=repo)
    except LexGuardError as exc:
        return _fail(document, exc.message, repo=repo)


async def process_url(
    *,
    user_id: str,
    url: str,
    document_type: DocumentType = DocumentType.TERMS_OF_SERVICE,
    repo: DocumentRepository | None = None,
) -> Document:
    repo = repo or _default_repo()
    document = Document(
        id=uuid.uuid4().hex,
        user_id=user_id,
        source=DocumentSource.URL,
        document_type=document_type,
        source_url=url,
    )
    try:
        page = await url_ingest.fetch_page(url)
        document.filename = page.title
        return _finalize(document, page.text, repo=repo)
    except LexGuardError as exc:
        return _fail(document, exc.message, repo=repo)

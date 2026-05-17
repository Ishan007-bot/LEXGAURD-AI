"""Tests for the document pipeline orchestrator.

We use an in-memory repo so Firestore is never touched, and we patch the
external extractors (Document AI, URL fetch) to return canned text.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.exceptions import UpstreamError
from app.models import (
    Document,
    DocumentStatus,
    DocumentType,
)
from app.repositories.documents import DocumentRepository
from app.services import pipeline
from app.services.url_ingest import IngestedPage


class _InMemoryRepo(DocumentRepository):
    def __init__(self) -> None:
        self.store: dict[str, Document] = {}

    def save(self, document: Document) -> None:
        self.store[document.id] = document.model_copy(deep=True)

    def get(self, *, document_id: str, user_id: str) -> Document:
        doc = self.store[document_id]
        assert doc.user_id == user_id
        return doc

    def list_for_user(self, *, user_id: str, limit: int = 20) -> list[Document]:
        return [d for d in self.store.values() if d.user_id == user_id][:limit]


SAMPLE = (
    "1. The Employee shall not engage in any non-compete activity for 3 years.\n"
    "2. All inventions shall be assigned to the Company without compensation.\n"
    "3. Either party may terminate this agreement upon thirty days notice.\n"
    "4. Any disputes shall be resolved by binding arbitration in Mumbai.\n"
)


def test_process_pasted_text_happy_path() -> None:
    repo = _InMemoryRepo()
    doc = pipeline.process_pasted_text(
        user_id="u1",
        text=SAMPLE,
        document_type=DocumentType.OFFER_LETTER,
        repo=repo,
    )
    assert doc.status == DocumentStatus.READY
    assert doc.user_id == "u1"
    assert len(doc.clauses) == 4
    # Categories should be inferred
    categories = {c.category.value for c in doc.clauses}
    assert "non_compete" in categories
    assert "termination" in categories
    # Persisted
    assert repo.get(document_id=doc.id, user_id="u1").status == DocumentStatus.READY


def test_process_uploaded_document_with_text_plain() -> None:
    repo = _InMemoryRepo()

    with patch("app.services.documentai.extract_text_from_gcs", return_value=SAMPLE):
        doc = pipeline.process_uploaded_document(
            document_id="doc-1",
            user_id="u1",
            gcs_object="users/u1/documents/doc-1/sample.txt",
            filename="sample.txt",
            content_type="text/plain",
            size_bytes=len(SAMPLE),
            repo=repo,
        )

    assert doc.status == DocumentStatus.READY
    assert doc.id == "doc-1"
    assert len(doc.clauses) == 4


def test_process_uploaded_document_marks_failed_on_extract_error() -> None:
    repo = _InMemoryRepo()

    def _boom(**_: object) -> str:
        raise UpstreamError("Document AI down")

    with patch("app.services.documentai.extract_text_from_gcs", side_effect=_boom):
        doc = pipeline.process_uploaded_document(
            document_id="doc-2",
            user_id="u1",
            gcs_object="x",
            filename="x.pdf",
            content_type="application/pdf",
            size_bytes=10,
            repo=repo,
        )
    assert doc.status == DocumentStatus.FAILED
    assert doc.failure_reason == "Document AI down"


@pytest.mark.asyncio
async def test_process_url_happy_path() -> None:
    repo = _InMemoryRepo()

    async def _fake_fetch(url: str) -> IngestedPage:
        return IngestedPage(url=url, title="Acme Terms", text=SAMPLE)

    with patch("app.services.url_ingest.fetch_page", side_effect=_fake_fetch):
        doc = await pipeline.process_url(
            user_id="u1",
            url="https://acme.example/terms",
            repo=repo,
        )

    assert doc.status == DocumentStatus.READY
    assert doc.filename == "Acme Terms"
    assert doc.source_url == "https://acme.example/terms"
    assert len(doc.clauses) == 4

"""Tests for the documents API routes.

Auth is overridden, the pipeline is patched, and the repo is replaced via the
patched pipeline so no GCP service is reached.
"""

from __future__ import annotations

from typing import Iterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthenticatedUser, require_user
from app.main import create_app
from app.models import (
    Clause,
    ClauseCategory,
    Document,
    DocumentSource,
    DocumentStatus,
    DocumentType,
)


def _user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="u1", email="t@t.test", name="Test")


@pytest.fixture
def authed() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[require_user] = _user
    with TestClient(app) as c:
        yield c


def _make_doc() -> Document:
    return Document(
        id="d-1",
        user_id="u1",
        source=DocumentSource.PASTED_TEXT,
        status=DocumentStatus.READY,
        document_type=DocumentType.OFFER_LETTER,
        clauses=[
            Clause(
                id="c1",
                index=0,
                text="The Employee shall not engage in non-compete activity.",
                category=ClauseCategory.NON_COMPETE,
                start_offset=0,
                end_offset=50,
            )
        ],
    )


def test_create_from_text(authed: TestClient) -> None:
    with patch("app.services.pipeline.process_pasted_text", return_value=_make_doc()):
        response = authed.post(
            "/documents/from-text",
            json={
                "text": "1. The Employee shall not engage in non-compete activity for 3 years. " * 2,
                "document_type": "offer_letter",
            },
        )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "d-1"
    assert body["status"] == "ready"
    assert body["clause_count"] == 1
    assert body["clauses"][0]["category"] == "non_compete"


def test_create_from_text_requires_auth() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/documents/from-text", json={"text": "x" * 30})
    assert response.status_code == 401


def test_create_from_url(authed: TestClient) -> None:
    async def _fake(**_kwargs: object) -> Document:
        return _make_doc()

    with patch("app.services.pipeline.process_url", side_effect=_fake):
        response = authed.post(
            "/documents/from-url",
            json={"url": "https://acme.example/terms"},
        )
    assert response.status_code == 201
    assert response.json()["id"] == "d-1"


def test_create_from_upload(authed: TestClient) -> None:
    with patch("app.services.pipeline.process_uploaded_document", return_value=_make_doc()):
        response = authed.post(
            "/documents/from-upload",
            json={
                "document_id": "d-1",
                "gcs_object": "users/u1/documents/d-1/file.pdf",
                "filename": "file.pdf",
                "content_type": "application/pdf",
                "size_bytes": 12345,
            },
        )
    assert response.status_code == 201
    assert response.json()["clauses"][0]["category"] == "non_compete"


def test_get_document(authed: TestClient) -> None:
    with patch(
        "app.routes.documents.FirestoreDocumentRepository"
    ) as repo_cls:
        repo_cls.return_value.get.return_value = _make_doc()
        response = authed.get("/documents/d-1")
    assert response.status_code == 200
    assert response.json()["id"] == "d-1"


def test_list_documents(authed: TestClient) -> None:
    with patch("app.routes.documents.FirestoreDocumentRepository") as repo_cls:
        repo_cls.return_value.list_for_user.return_value = [_make_doc()]
        response = authed.get("/documents?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == "d-1"

"""Firestore-backed repository for documents.

The repository hides Firestore from callers — services receive and return
plain `Document` models, never `DocumentReference` or `DocumentSnapshot`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from app.clients.gcp import get_firestore_client
from app.config import get_settings
from app.exceptions import NotFoundError, UpstreamError
from app.models import Document

if TYPE_CHECKING:  # pragma: no cover
    from google.cloud.firestore import CollectionReference


class DocumentRepository(Protocol):
    def save(self, document: Document) -> None: ...
    def get(self, *, document_id: str, user_id: str) -> Document: ...
    def list_for_user(self, *, user_id: str, limit: int = 20) -> list[Document]: ...


# ---------------------------------------------------------------------------


class FirestoreDocumentRepository:
    """Firestore implementation backed by the `documents` collection."""

    def __init__(self) -> None:
        self._settings = get_settings()

    # Resolved lazily so unit tests can patch `get_firestore_client`.
    def _collection(self) -> "CollectionReference":
        client = get_firestore_client()
        return client.collection(self._settings.firestore_collection_documents)

    def save(self, document: Document) -> None:
        document.touch()
        payload = document.model_dump(mode="json")
        try:
            self._collection().document(document.id).set(payload, merge=False)
        except Exception as exc:  # noqa: BLE001
            raise UpstreamError("Failed to persist document.") from exc

    def get(self, *, document_id: str, user_id: str) -> Document:
        try:
            snap = self._collection().document(document_id).get()
        except Exception as exc:  # noqa: BLE001
            raise UpstreamError("Failed to load document.") from exc

        if not snap.exists:
            raise NotFoundError("Document not found.")
        data = snap.to_dict() or {}
        if data.get("user_id") != user_id:
            # Don't leak existence of other users' documents.
            raise NotFoundError("Document not found.")
        return Document.model_validate(data)

    def list_for_user(self, *, user_id: str, limit: int = 20) -> list[Document]:
        try:
            query = (
                self._collection()
                .where("user_id", "==", user_id)
                .order_by("created_at", direction="DESCENDING")
                .limit(limit)
            )
            snaps = query.stream()
        except Exception as exc:  # noqa: BLE001
            raise UpstreamError("Failed to list documents.") from exc

        results: list[Document] = []
        for snap in snaps:
            data = snap.to_dict() or {}
            results.append(Document.model_validate(data))
        return results

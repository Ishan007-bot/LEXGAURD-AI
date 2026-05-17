"""Firestore-backed repository for document analyses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from app.clients.gcp import get_firestore_client
from app.config import get_settings
from app.exceptions import NotFoundError, UpstreamError
from app.models import DocumentAnalysis

if TYPE_CHECKING:  # pragma: no cover
    from google.cloud.firestore import CollectionReference


class AnalysisRepository(Protocol):
    def save(self, analysis: DocumentAnalysis) -> None: ...
    def get(self, *, analysis_id: str, user_id: str) -> DocumentAnalysis: ...
    def list_for_document(self, *, document_id: str, user_id: str) -> list[DocumentAnalysis]: ...


class FirestoreAnalysisRepository:
    def __init__(self) -> None:
        self._settings = get_settings()

    def _collection(self) -> "CollectionReference":
        return get_firestore_client().collection(self._settings.firestore_collection_analyses)

    def save(self, analysis: DocumentAnalysis) -> None:
        analysis.touch()
        try:
            self._collection().document(analysis.id).set(
                analysis.model_dump(mode="json"), merge=False
            )
        except Exception as exc:  # noqa: BLE001
            raise UpstreamError("Failed to persist analysis.") from exc

    def get(self, *, analysis_id: str, user_id: str) -> DocumentAnalysis:
        try:
            snap = self._collection().document(analysis_id).get()
        except Exception as exc:  # noqa: BLE001
            raise UpstreamError("Failed to load analysis.") from exc
        if not snap.exists:
            raise NotFoundError("Analysis not found.")
        data = snap.to_dict() or {}
        if data.get("user_id") != user_id:
            raise NotFoundError("Analysis not found.")
        return DocumentAnalysis.model_validate(data)

    def list_for_document(
        self, *, document_id: str, user_id: str
    ) -> list[DocumentAnalysis]:
        try:
            snaps = (
                self._collection()
                .where("document_id", "==", document_id)
                .where("user_id", "==", user_id)
                .order_by("created_at", direction="DESCENDING")
                .stream()
            )
        except Exception as exc:  # noqa: BLE001
            raise UpstreamError("Failed to list analyses.") from exc
        results: list[DocumentAnalysis] = []
        for snap in snaps:
            results.append(DocumentAnalysis.model_validate(snap.to_dict() or {}))
        return results

"""Test stubs for the LLM client and repositories."""

from __future__ import annotations

from collections.abc import Iterator

from pydantic import BaseModel

from app.agents.state import (
    DefenderOutput,
    JudgeOutput,
    NegotiatorOutput,
    ProsecutorOutput,
)
from app.models import (
    Document,
    DocumentAnalysis,
    Severity,
)
from app.repositories.analyses import AnalysisRepository
from app.repositories.documents import DocumentRepository
from app.services.vertex import LLMClient


class StubLLMClient(LLMClient):
    """Returns canned outputs keyed by schema_type.

    Each value is consumed in FIFO order from a list; if exhausted, the
    fallback is reused. Also records every call for assertions.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.responses: dict[type[BaseModel], list[BaseModel]] = {}
        self.fallbacks: dict[type[BaseModel], BaseModel] = {
            ProsecutorOutput: ProsecutorOutput(
                preliminary_severity=Severity.MEDIUM,
                argument="Stub: this clause has some asymmetry.",
                concerns=["asymmetric obligations"],
            ),
            DefenderOutput: DefenderOutput(
                argument="Stub: this is standard industry practice.",
                industry_references=["typical SaaS terms"],
            ),
            JudgeOutput: JudgeOutput(
                severity=Severity.MEDIUM,
                risk_score=50,
                plain_english="Stub: notable but not a deal-breaker.",
                reasoning="Stub reasoning weighing both arguments.",
                citations=["Stub citation"],
            ),
            NegotiatorOutput: NegotiatorOutput(
                suggested_redline="Stub redline text.",
                plain_english_explanation="Stub explanation.",
                walk_away=False,
            ),
        }

    def queue(self, schema_type: type[BaseModel], response: BaseModel) -> None:
        self.responses.setdefault(schema_type, []).append(response)

    async def generate_structured(  # type: ignore[override]
        self,
        *,
        tier: str,
        system: str,
        user: str,
        schema_type: type,
    ):
        self.calls.append({"tier": tier, "schema": schema_type.__name__, "user": user})
        bucket = self.responses.get(schema_type)
        if bucket:
            return bucket.pop(0)
        return self.fallbacks[schema_type]


class InMemoryDocumentRepo(DocumentRepository):
    def __init__(self) -> None:
        self.store: dict[str, Document] = {}

    def save(self, document: Document) -> None:
        self.store[document.id] = document.model_copy(deep=True)

    def get(self, *, document_id: str, user_id: str) -> Document:
        doc = self.store[document_id]
        assert doc.user_id == user_id
        return doc.model_copy(deep=True)

    def list_for_user(self, *, user_id: str, limit: int = 20) -> list[Document]:
        return [d for d in self.store.values() if d.user_id == user_id][:limit]


class InMemoryAnalysisRepo(AnalysisRepository):
    def __init__(self) -> None:
        self.store: dict[str, DocumentAnalysis] = {}

    def save(self, analysis: DocumentAnalysis) -> None:
        self.store[analysis.id] = analysis.model_copy(deep=True)

    def get(self, *, analysis_id: str, user_id: str) -> DocumentAnalysis:
        a = self.store[analysis_id]
        assert a.user_id == user_id
        return a.model_copy(deep=True)

    def list_for_document(
        self, *, document_id: str, user_id: str
    ) -> list[DocumentAnalysis]:
        return [
            a
            for a in self.store.values()
            if a.document_id == document_id and a.user_id == user_id
        ]


def iter_severities() -> Iterator[Severity]:
    for s in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO):
        yield s

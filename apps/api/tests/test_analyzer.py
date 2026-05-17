"""Tests for the analyzer service.

These exercise the full per-clause pipeline (Defender → Judge → Negotiator)
with the StubLLMClient — no Vertex traffic, no Firestore traffic.
"""

from __future__ import annotations

import pytest

from app.agents.state import (
    DefenderOutput,
    JudgeOutput,
    NegotiatorOutput,
    ProsecutorOutput,
)
from app.exceptions import ValidationError
from app.models import (
    AnalysisStatus,
    Clause,
    ClauseCategory,
    Document,
    DocumentSource,
    DocumentStatus,
    DocumentType,
    Severity,
)
from app.services import analyzer
from app.services.vertex import ModelTier
from tests.stubs import InMemoryAnalysisRepo, InMemoryDocumentRepo, StubLLMClient


def _doc_with_clauses(n: int = 5) -> Document:
    return Document(
        id="d1",
        user_id="u1",
        source=DocumentSource.PASTED_TEXT,
        status=DocumentStatus.READY,
        document_type=DocumentType.OFFER_LETTER,
        clauses=[
            Clause(
                id=f"c{i}",
                index=i,
                text=f"Clause number {i} requires the employee to do X for Y years without notice.",
                category=ClauseCategory.OTHER,
                start_offset=i * 100,
                end_offset=i * 100 + 80,
            )
            for i in range(n)
        ],
    )


@pytest.mark.asyncio
async def test_analyze_happy_path() -> None:
    doc_repo = InMemoryDocumentRepo()
    analy_repo = InMemoryAnalysisRepo()
    doc = _doc_with_clauses(4)
    doc_repo.save(doc)

    client = StubLLMClient()
    analysis = await analyzer.analyze_document(
        document_id=doc.id,
        user_id="u1",
        document_repo=doc_repo,
        analysis_repo=analy_repo,
        llm_client=client,
    )

    assert analysis.status is AnalysisStatus.READY
    assert len(analysis.clauses) == 4
    assert 0 <= analysis.overall_risk_score <= 100
    # Each clause should have at least Judge in its debate
    for ca in analysis.clauses:
        agents_in_debate = {t.agent.value for t in ca.debate}
        assert "judge" in agents_in_debate
    # Persisted
    assert analy_repo.get(analysis_id=analysis.id, user_id="u1").status is AnalysisStatus.READY


@pytest.mark.asyncio
async def test_pro_judge_used_for_top_n() -> None:
    """The top-3 prosecutor severities should escalate to the Pro model."""
    doc_repo = InMemoryDocumentRepo()
    analy_repo = InMemoryAnalysisRepo()
    doc = _doc_with_clauses(5)
    doc_repo.save(doc)

    client = StubLLMClient()
    severities = [
        Severity.CRITICAL,
        Severity.HIGH,
        Severity.MEDIUM,
        Severity.LOW,
        Severity.INFO,
    ]
    for sev in severities:
        client.queue(
            ProsecutorOutput,
            ProsecutorOutput(preliminary_severity=sev, argument="x" * 30),
        )

    await analyzer.analyze_document(
        document_id=doc.id,
        user_id="u1",
        document_repo=doc_repo,
        analysis_repo=analy_repo,
        llm_client=client,
    )

    judge_calls = [c for c in client.calls if c["schema"] == "JudgeOutput"]
    pro_calls = [c for c in judge_calls if c["tier"] == ModelTier.PRO]
    flash_calls = [c for c in judge_calls if c["tier"] == ModelTier.FLASH]
    assert len(pro_calls) == 3, "Pro should only be used for the top-3 risky clauses"
    assert len(flash_calls) == 2


@pytest.mark.asyncio
async def test_rejects_document_not_ready() -> None:
    doc_repo = InMemoryDocumentRepo()
    analy_repo = InMemoryAnalysisRepo()
    doc = _doc_with_clauses(1)
    doc.status = DocumentStatus.PROCESSING
    doc_repo.save(doc)

    with pytest.raises(ValidationError):
        await analyzer.analyze_document(
            document_id=doc.id,
            user_id="u1",
            document_repo=doc_repo,
            analysis_repo=analy_repo,
            llm_client=StubLLMClient(),
        )


@pytest.mark.asyncio
async def test_rejects_too_many_clauses() -> None:
    doc_repo = InMemoryDocumentRepo()
    doc = _doc_with_clauses(analyzer.MAX_CLAUSES_PER_DOC + 1)
    doc_repo.save(doc)

    with pytest.raises(ValidationError):
        await analyzer.analyze_document(
            document_id=doc.id,
            user_id="u1",
            document_repo=doc_repo,
            analysis_repo=InMemoryAnalysisRepo(),
            llm_client=StubLLMClient(),
        )


@pytest.mark.asyncio
async def test_negotiator_skipped_for_low_severity() -> None:
    doc_repo = InMemoryDocumentRepo()
    analy_repo = InMemoryAnalysisRepo()
    doc = _doc_with_clauses(2)
    doc_repo.save(doc)

    client = StubLLMClient()
    # All judges return LOW → negotiator should not be called.
    client.queue(JudgeOutput, JudgeOutput(
        severity=Severity.LOW,
        risk_score=20,
        plain_english="Low risk." + " " * 5,
        reasoning="Both sides agree this is benign." + " " * 5,
    ))
    client.queue(JudgeOutput, JudgeOutput(
        severity=Severity.LOW,
        risk_score=15,
        plain_english="Low risk again." + " " * 5,
        reasoning="Nothing to see here." + " " * 5,
    ))
    # Defender stubs (one per clause)
    for _ in range(2):
        client.queue(DefenderOutput, DefenderOutput(argument="Standard." + " " * 30))

    await analyzer.analyze_document(
        document_id=doc.id,
        user_id="u1",
        document_repo=doc_repo,
        analysis_repo=analy_repo,
        llm_client=client,
    )

    negotiator_calls = [c for c in client.calls if c["schema"] == "NegotiatorOutput"]
    assert negotiator_calls == []


def test_overall_score_helpers() -> None:
    # Pure functions — quick sanity check.
    assert analyzer._overall_score([]) == 0
    summary = analyzer._summary([], 0)
    assert "No clauses" in summary

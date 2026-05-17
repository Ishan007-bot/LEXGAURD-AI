"""Tests for the What-If simulator service and route."""

from __future__ import annotations

from typing import Iterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.agents.state import ScenarioOutput
from app.auth import AuthenticatedUser, require_user
from app.exceptions import ValidationError
from app.main import create_app
from app.models import (
    AnalysisStatus,
    Clause,
    ClauseAnalysis,
    ClauseCategory,
    Document,
    DocumentAnalysis,
    DocumentSource,
    DocumentStatus,
    DocumentType,
    Severity,
)
from app.services import simulator
from tests.stubs import InMemoryAnalysisRepo, InMemoryDocumentRepo, StubLLMClient


def _seed(doc_repo: InMemoryDocumentRepo, analy_repo: InMemoryAnalysisRepo) -> None:
    clauses = [
        Clause(id=f"c{i}", index=i, text=f"Clause {i} text body for testing.",
               category=ClauseCategory.OTHER, start_offset=i * 100, end_offset=i * 100 + 40)
        for i in range(3)
    ]
    doc = Document(
        id="d1", user_id="u1", source=DocumentSource.PASTED_TEXT,
        status=DocumentStatus.READY, document_type=DocumentType.OFFER_LETTER,
        clauses=clauses,
    )
    doc_repo.save(doc)
    analysis = DocumentAnalysis(
        id="a1", document_id="d1", user_id="u1", status=AnalysisStatus.READY,
        overall_risk_score=70, summary="High-risk offer letter.",
        clauses=[
            ClauseAnalysis(
                clause_id=f"c{i}",
                severity=[Severity.CRITICAL, Severity.MEDIUM, Severity.LOW][i],
                risk_score=80 - i * 20,
                plain_english=f"Plain {i}.",
            )
            for i in range(3)
        ],
    )
    analy_repo.save(analysis)


@pytest.mark.asyncio
async def test_simulate_returns_scenario_output() -> None:
    doc_repo = InMemoryDocumentRepo()
    analy_repo = InMemoryAnalysisRepo()
    _seed(doc_repo, analy_repo)
    client = StubLLMClient()

    result = await simulator.simulate(
        analysis_id="a1",
        user_id="u1",
        scenario="What if I quit after 6 months?",
        document_repo=doc_repo,
        analysis_repo=analy_repo,
        llm_client=client,
    )
    assert isinstance(result, ScenarioOutput)
    assert result.headline
    assert result.consequences
    assert "What if I quit after 6 months?" in str(client.calls[-1]["user"])


@pytest.mark.asyncio
async def test_simulate_rejects_empty_scenario() -> None:
    with pytest.raises(ValidationError):
        await simulator.simulate(
            analysis_id="a1",
            user_id="u1",
            scenario="   ",
            document_repo=InMemoryDocumentRepo(),
            analysis_repo=InMemoryAnalysisRepo(),
            llm_client=StubLLMClient(),
        )


@pytest.mark.asyncio
async def test_simulate_rejects_overlong_scenario() -> None:
    with pytest.raises(ValidationError):
        await simulator.simulate(
            analysis_id="a1",
            user_id="u1",
            scenario="x" * 600,
            document_repo=InMemoryDocumentRepo(),
            analysis_repo=InMemoryAnalysisRepo(),
            llm_client=StubLLMClient(),
        )


# ---- route ----------------------------------------------------------------


def _user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="u1", email="t@t.test", name="T")


@pytest.fixture
def auth_client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[require_user] = _user
    with TestClient(app) as c:
        yield c


def test_simulate_route(auth_client: TestClient) -> None:
    async def _fake(**_: object) -> ScenarioOutput:
        return ScenarioOutput(
            headline="You owe two months of salary back.",
            consequences=["Clause 1 triggers a six-month non-compete on top of clawback."],
            severity=Severity.HIGH,
            advice="Demand a payback cap in writing before signing.",
        )

    with patch("app.services.simulator.simulate", side_effect=_fake):
        response = auth_client.post(
            "/analyses/a1/simulate",
            json={"scenario": "What if I quit after 6 months?"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["severity"] == "high"
    assert "non-compete" in body["consequences"][0]

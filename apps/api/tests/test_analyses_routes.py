"""Tests for the /documents/{id}/analyses route family."""

from __future__ import annotations

from typing import Iterator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthenticatedUser, require_user
from app.main import create_app
from app.models import (
    AgentName,
    AgentTurn,
    AnalysisStatus,
    ClauseAnalysis,
    DocumentAnalysis,
    Severity,
)


def _user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="u1", email="t@t.test", name="T")


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[require_user] = _user
    with TestClient(app) as c:
        yield c


def _analysis() -> DocumentAnalysis:
    return DocumentAnalysis(
        id="a1",
        document_id="d1",
        user_id="u1",
        status=AnalysisStatus.READY,
        overall_risk_score=72,
        summary="3 high-risk clauses.",
        clauses=[
            ClauseAnalysis(
                clause_id="c1",
                severity=Severity.HIGH,
                risk_score=78,
                plain_english="Non-compete is too long.",
                debate=[
                    AgentTurn(agent=AgentName.PROSECUTOR, argument="Unenforceable"),
                    AgentTurn(agent=AgentName.JUDGE, argument="Verdict reasoning"),
                ],
                suggested_redline="Limit to 6 months.",
                citations=["Indian Contract Act §27"],
            )
        ],
    )


def test_create_analysis_route(client: TestClient) -> None:
    async def _fake(**_kwargs: object) -> DocumentAnalysis:
        return _analysis()

    with patch("app.services.analyzer.analyze_document", side_effect=_fake):
        response = client.post("/documents/d1/analyses")
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "a1"
    assert body["overall_risk_score"] == 72
    assert body["clauses"][0]["severity"] == "high"
    assert body["clauses"][0]["debate"][0]["agent"] == "prosecutor"


def test_get_analysis_route(client: TestClient) -> None:
    with patch("app.routes.analyses.FirestoreAnalysisRepository") as repo_cls:
        repo_cls.return_value.get.return_value = _analysis()
        response = client.get("/analyses/a1")
    assert response.status_code == 200
    assert response.json()["id"] == "a1"


def test_list_analyses_route(client: TestClient) -> None:
    with patch("app.routes.analyses.FirestoreAnalysisRepository") as repo_cls:
        repo_cls.return_value.list_for_document.return_value = [_analysis()]
        response = client.get("/documents/d1/analyses")
    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "a1"


def test_create_requires_auth() -> None:
    app = create_app()
    with TestClient(app) as c:
        assert c.post("/documents/d1/analyses").status_code == 401

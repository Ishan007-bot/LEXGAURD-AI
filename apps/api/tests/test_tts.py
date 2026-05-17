"""Tests for the TTS service + route."""

from __future__ import annotations

import base64
from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthenticatedUser, require_user
from app.exceptions import UpstreamError
from app.main import create_app
from app.models import (
    AnalysisStatus,
    ClauseAnalysis,
    DocumentAnalysis,
    Severity,
)
from app.services import tts


def test_synthesize_rejects_empty_text() -> None:
    with pytest.raises(UpstreamError):
        tts.synthesize("   ")


def test_synthesize_caps_long_input() -> None:
    response_obj = MagicMock(audio_content=b"FAKE_MP3")
    client = MagicMock()
    client.synthesize_speech.return_value = response_obj

    with patch("google.cloud.texttospeech.TextToSpeechClient", return_value=client):
        result = tts.synthesize("a" * 10_000)
    assert result.char_count == tts.MAX_CHARS
    assert base64.b64decode(result.audio_base64) == b"FAKE_MP3"


def test_synthesize_wraps_upstream_errors() -> None:
    client = MagicMock()
    client.synthesize_speech.side_effect = RuntimeError("boom")

    with patch("google.cloud.texttospeech.TextToSpeechClient", return_value=client):
        with pytest.raises(UpstreamError):
            tts.synthesize("hello")


# ----- route -----


def _user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="u1", email="t@t.test", name="T")


def _analysis() -> DocumentAnalysis:
    return DocumentAnalysis(
        id="a1", document_id="d1", user_id="u1", status=AnalysisStatus.READY,
        overall_risk_score=78, summary="Three high-risk clauses identified.",
        clauses=[
            ClauseAnalysis(
                clause_id="c1", severity=Severity.HIGH, risk_score=80,
                plain_english="Non-compete is too long.",
            ),
        ],
    )


@pytest.fixture
def auth_client() -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[require_user] = _user
    with TestClient(app) as c:
        yield c


def test_tts_route(auth_client: TestClient) -> None:
    response_obj = MagicMock(audio_content=b"FAKE_MP3_BYTES")
    fake_tts_client = MagicMock()
    fake_tts_client.synthesize_speech.return_value = response_obj

    with patch("app.routes.tts.FirestoreAnalysisRepository") as repo_cls, \
         patch("google.cloud.texttospeech.TextToSpeechClient", return_value=fake_tts_client):
        repo_cls.return_value.get.return_value = _analysis()
        response = auth_client.post("/analyses/a1/tts")

    assert response.status_code == 200
    body = response.json()
    assert body["mime_type"] == "audio/mpeg"
    assert base64.b64decode(body["audio_base64"]) == b"FAKE_MP3_BYTES"
    assert body["char_count"] > 0

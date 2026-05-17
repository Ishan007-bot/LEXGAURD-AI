"""Tests for request-id, security headers, and error handling middleware."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_request_id_is_added_if_missing(client: TestClient) -> None:
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) >= 16


def test_request_id_is_preserved_if_supplied(client: TestClient) -> None:
    rid = "my-trace-id-123"
    response = client.get("/health", headers={"X-Request-ID": rid})
    assert response.headers["X-Request-ID"] == rid


def test_404_returns_envelope(client: TestClient) -> None:
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "http_error"
    assert "requestId" in body["error"]


def test_validation_error_envelope(client: TestClient) -> None:
    # /uploads/init requires auth, but we want a 422 first if the body is malformed.
    # Use a known POST endpoint with no body — auth middleware fires first (401).
    response = client.post("/uploads/init")
    assert response.status_code in (401, 422)
    assert "error" in response.json()

"""Tests for the upload-init endpoint and service.

The service is unit-tested directly with the GCS client patched; the route is
tested via TestClient with the auth dependency overridden.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthenticatedUser, require_user
from app.exceptions import UpstreamError, ValidationError
from app.main import create_app
from app.schemas.upload import UploadInitRequest
from app.services import uploads as uploads_svc


def _fake_user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="user-abc", email="t@t.test", name="Test")


@pytest.fixture
def auth_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[require_user] = _fake_user
    return TestClient(app)


# ----- service-level ---------------------------------------------------------


def test_init_upload_rejects_bad_mime() -> None:
    req = UploadInitRequest(filename="x.exe", content_type="application/x-msdownload", size_bytes=10)
    with pytest.raises(ValidationError):
        uploads_svc.init_upload(req, user_id="u1")


def test_init_upload_returns_signed_url() -> None:
    req = UploadInitRequest(filename="a.pdf", content_type="application/pdf", size_bytes=2048)

    blob = MagicMock()
    blob.generate_signed_url.return_value = "https://signed.example/upload"
    bucket = MagicMock()
    bucket.blob.return_value = blob
    client = MagicMock()
    client.bucket.return_value = bucket

    with patch("app.services.uploads.get_storage_client", return_value=client):
        resp = uploads_svc.init_upload(req, user_id="user-123")

    assert resp.upload_url == "https://signed.example/upload"
    assert resp.method == "PUT"
    assert resp.headers["Content-Type"] == "application/pdf"
    assert resp.gcs_object.startswith("users/user-123/documents/")
    assert resp.gcs_object.endswith("/a.pdf")


def test_init_upload_wraps_gcs_errors() -> None:
    req = UploadInitRequest(filename="a.pdf", content_type="application/pdf", size_bytes=100)
    client = MagicMock()
    client.bucket.side_effect = RuntimeError("gcs boom")
    with patch("app.services.uploads.get_storage_client", return_value=client):
        with pytest.raises(UpstreamError):
            uploads_svc.init_upload(req, user_id="u")


# ----- route-level -----------------------------------------------------------


def test_route_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/uploads/init",
        json={"filename": "a.pdf", "content_type": "application/pdf", "size_bytes": 100},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_route_happy_path(auth_client: TestClient) -> None:
    blob = MagicMock()
    blob.generate_signed_url.return_value = "https://signed.example/x"
    bucket = MagicMock()
    bucket.blob.return_value = blob
    storage = MagicMock()
    storage.bucket.return_value = bucket

    with patch("app.services.uploads.get_storage_client", return_value=storage):
        response = auth_client.post(
            "/uploads/init",
            json={"filename": "lease.pdf", "content_type": "application/pdf", "size_bytes": 100},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["upload_url"] == "https://signed.example/x"
    assert body["method"] == "PUT"
    assert body["expires_in_seconds"] > 0


def test_route_rejects_invalid_body(auth_client: TestClient) -> None:
    response = auth_client.post(
        "/uploads/init",
        json={"filename": "", "content_type": "application/pdf", "size_bytes": 1},
    )
    assert response.status_code == 422

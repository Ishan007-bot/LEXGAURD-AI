"""Tests for the regex-based redaction layer."""

from __future__ import annotations

from app.services.dlp import redact, redact_regex


def test_redacts_email() -> None:
    out = redact_regex("Contact me at jane.doe+work@example.co.in tomorrow.")
    assert "[REDACTED_EMAIL]" in out
    assert "jane.doe" not in out


def test_redacts_pan() -> None:
    out = redact_regex("PAN: ABCDE1234F is on file.")
    assert "[REDACTED_PAN]" in out
    assert "ABCDE1234F" not in out


def test_redacts_aadhaar() -> None:
    out = redact_regex("Aadhaar 1234 5678 9012 provided.")
    assert "[REDACTED_AADHAAR]" in out


def test_idempotent() -> None:
    once = redact_regex("a@b.com")
    twice = redact_regex(once)
    assert once == twice


def test_redact_no_cloud_call_by_default() -> None:
    # Should not raise even though no GCP project / creds are set.
    out = redact("plain text with no pii")
    assert out == "plain text with no pii"

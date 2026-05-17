"""Cloud DLP redaction wrapper with a local-regex fallback.

We always run a regex-based redaction pass for two reasons:

1. **Cost control.** Calling DLP on every clause would burn the $5 budget fast.
   The regex pass handles the long tail of trivial PII (emails, phone numbers,
   credit cards, IDs) for free.
2. **Defense in depth.** Even when DLP is enabled, regex catches India-specific
   identifiers (PAN, Aadhaar) that DLP's default infoTypes may miss.

The full Cloud DLP call is used only on the *first* (longest) extraction so we
get its richer detector list. After that, redaction is regex-only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import get_settings
from app.exceptions import UpstreamError
from app.logging_setup import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _Detector:
    name: str
    pattern: re.Pattern[str]
    placeholder: str


# Order matters — longest / most specific first.
_DETECTORS: tuple[_Detector, ...] = (
    _Detector(
        "EMAIL",
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.IGNORECASE),
        "[REDACTED_EMAIL]",
    ),
    _Detector(
        "CREDIT_CARD",
        re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        "[REDACTED_CARD]",
    ),
    _Detector(
        "PAN",  # India: ABCDE1234F
        re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
        "[REDACTED_PAN]",
    ),
    _Detector(
        "AADHAAR",  # 12 digits, optionally space-grouped 4-4-4
        re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
        "[REDACTED_AADHAAR]",
    ),
    _Detector(
        "PHONE",
        re.compile(
            r"(?:\+?\d{1,3}[ -]?)?(?:\(?\d{2,4}\)?[ -]?)?\d{3,4}[ -]?\d{3,4}\b"
        ),
        "[REDACTED_PHONE]",
    ),
)

# DLP infoTypes we'll request from the cloud API for the high-quality pass.
_DLP_INFO_TYPES: tuple[str, ...] = (
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD_NUMBER",
    "IBAN_CODE",
    "PERSON_NAME",
    "STREET_ADDRESS",
    "IP_ADDRESS",
    "DATE_OF_BIRTH",
)


def redact_regex(text: str) -> str:
    """Cheap, deterministic local redaction. Always safe to call."""
    out = text
    for det in _DETECTORS:
        out = det.pattern.sub(det.placeholder, out)
    return out


def _redact_dlp(text: str) -> str:
    """Call Cloud DLP and replace findings with placeholders.

    Falls back to regex on error — we never want a DLP outage to block analysis.
    """
    from google.cloud import dlp_v2

    settings = get_settings()
    client = dlp_v2.DlpServiceClient()
    parent = f"projects/{settings.gcp_project_id}/locations/global"

    info_types = [{"name": t} for t in _DLP_INFO_TYPES]
    inspect_config = {"info_types": info_types, "min_likelihood": dlp_v2.Likelihood.LIKELY}
    deidentify_config = {
        "info_type_transformations": {
            "transformations": [
                {
                    "primitive_transformation": {
                        "replace_with_info_type_config": {},
                    },
                },
            ]
        }
    }

    try:
        response = client.deidentify_content(
            request={
                "parent": parent,
                "deidentify_config": deidentify_config,
                "inspect_config": inspect_config,
                "item": {"value": text},
            }
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("dlp.deidentify_failed_falling_back_to_regex", error=str(exc))
        return redact_regex(text)

    return response.item.value or text


def redact(text: str, *, use_cloud_dlp: bool = False) -> str:
    """Redact PII from `text`.

    `use_cloud_dlp=True` runs the Cloud DLP pass first (slower, costs $$),
    followed by the regex pass to catch India-specific tokens. Default is
    `False` to fit the $5 budget — see docs/budget.md.
    """
    if not text:
        return text
    if use_cloud_dlp:
        try:
            text = _redact_dlp(text)
        except UpstreamError:  # pragma: no cover — only if we re-raise upstream
            pass
    return redact_regex(text)

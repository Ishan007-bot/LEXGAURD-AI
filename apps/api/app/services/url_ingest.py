"""Fetch a public URL and extract readable text from it.

Used to ingest "online policies" — privacy policies, T&Cs, ticket terms — that
live as web pages instead of files. The user pastes a URL; we fetch it once and
hand the plain text to the rest of the pipeline.

Security:
- HTTPS only.
- No redirects to private IPs (Cloud Run's egress is already public-only, but
  we still reject obvious loopback / RFC1918 hostnames defensively).
- 5 MiB response cap to prevent memory abuse.
- 15-second timeout.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.exceptions import UpstreamError, ValidationError
from app.logging_setup import get_logger

logger = get_logger(__name__)

MAX_BYTES = 5 * 1024 * 1024
TIMEOUT_SECONDS = 15.0
USER_AGENT = "LexGuardBot/0.1 (+https://lexguard.invalid)"

_BLOCKED_TAGS = {"script", "style", "noscript", "iframe", "svg", "form", "header", "footer", "nav"}
_WHITESPACE_RE = re.compile(r"[ \t]+")
_BLANKLINES_RE = re.compile(r"\n{3,}")


@dataclass(frozen=True, slots=True)
class IngestedPage:
    url: str
    title: str | None
    text: str


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValidationError("Only http(s) URLs are supported.")
    host = parsed.hostname or ""
    if not host:
        raise ValidationError("URL is missing a host.")
    # Reject obvious internal hosts. We can't resolve DNS here without
    # opening up SSRF avenues; this catches the trivial typed-IP case.
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValidationError("URL host is not allowed.")
    except ValueError:
        pass
    return url


def _clean_text(html: str) -> tuple[str | None, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag_name in _BLOCKED_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    title = (soup.title.string.strip() if soup.title and soup.title.string else None)
    body = soup.body or soup
    text = body.get_text(separator="\n", strip=True)
    text = _WHITESPACE_RE.sub(" ", text)
    text = _BLANKLINES_RE.sub("\n\n", text).strip()
    return title, text


async def fetch_page(url: str) -> IngestedPage:
    safe_url = _validate_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT_SECONDS, follow_redirects=True, headers=headers
        ) as client:
            response = await client.get(safe_url)
    except httpx.HTTPError as exc:
        logger.warning("url_ingest.request_failed", url=safe_url, error=str(exc))
        raise UpstreamError("Could not fetch the URL.") from exc

    if response.status_code >= 400:
        raise UpstreamError(f"URL returned HTTP {response.status_code}.")

    if len(response.content) > MAX_BYTES:
        raise ValidationError("Page is too large to process (>5 MiB).")

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        raise ValidationError(f"Unsupported content type: {content_type!r}")

    title, text = _clean_text(response.text)
    if len(text) < 100:
        raise ValidationError("Page text is too short — is this the right URL?")

    return IngestedPage(url=safe_url, title=title, text=text)

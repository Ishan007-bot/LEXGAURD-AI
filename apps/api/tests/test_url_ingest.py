"""Tests for the URL ingestion service.

httpx is patched via `respx` so the suite runs offline.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from app.exceptions import UpstreamError, ValidationError
from app.services.url_ingest import fetch_page


def test_rejects_non_http_scheme() -> None:
    with pytest.raises(ValidationError):
        import asyncio

        asyncio.run(fetch_page("ftp://example.com"))


def test_rejects_loopback() -> None:
    import asyncio

    with pytest.raises(ValidationError):
        asyncio.run(fetch_page("http://127.0.0.1/terms"))


@pytest.mark.asyncio
async def test_happy_path() -> None:
    html = """
    <html>
      <head><title>Acme Terms</title></head>
      <body>
        <header>nav</header>
        <main>
          <h1>Terms of Service</h1>
          <p>By using Acme you agree to be bound by these terms and conditions.</p>
          <p>We may modify these terms at any time and without notice to you.</p>
          <script>tracking()</script>
        </main>
        <footer>(c)</footer>
      </body>
    </html>
    """
    async with respx.mock(assert_all_called=True) as mock:
        mock.get("https://acme.example/terms").mock(
            return_value=httpx.Response(
                200,
                text=html,
                headers={"content-type": "text/html; charset=utf-8"},
            )
        )
        page = await fetch_page("https://acme.example/terms")

    assert page.title == "Acme Terms"
    assert "Terms of Service" in page.text
    assert "tracking()" not in page.text
    assert "nav" not in page.text


@pytest.mark.asyncio
async def test_4xx_raises_upstream() -> None:
    async with respx.mock(assert_all_called=True) as mock:
        mock.get("https://acme.example/missing").mock(return_value=httpx.Response(404, text=""))
        with pytest.raises(UpstreamError):
            await fetch_page("https://acme.example/missing")


@pytest.mark.asyncio
async def test_rejects_non_html_content_type() -> None:
    async with respx.mock(assert_all_called=True) as mock:
        mock.get("https://acme.example/file.pdf").mock(
            return_value=httpx.Response(
                200,
                text="PDF binary",
                headers={"content-type": "application/pdf"},
            )
        )
        with pytest.raises(ValidationError):
            await fetch_page("https://acme.example/file.pdf")

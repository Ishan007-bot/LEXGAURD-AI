"""LLM client abstraction over Vertex AI Gemini.

The agents depend on the `LLMClient` Protocol — tests inject a stub, prod uses
`VertexLLMClient`. This keeps the test suite offline and the cost at $0
during development.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError as PydValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings
from app.exceptions import UpstreamError
from app.logging_setup import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class ModelTier:
    """Logical model identifiers — actual Gemini IDs resolved at call time."""

    FLASH = "flash"
    PRO = "pro"


class LLMClient(Protocol):
    """Minimal interface every agent uses."""

    async def generate_structured(
        self,
        *,
        tier: str,
        system: str,
        user: str,
        schema_type: type[T],
    ) -> T:
        """Return a Pydantic instance of `schema_type`."""
        ...


# ---------- Vertex implementation -------------------------------------------


class VertexLLMClient:
    """Production LLM client using Vertex AI Gemini."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._initialised = False

    def _ensure_init(self) -> None:
        if self._initialised:
            return
        import vertexai  # lazy import to keep tests light

        vertexai.init(
            project=self._settings.gcp_project_id,
            location=self._settings.vertex_location,
        )
        self._initialised = True

    def _model_id(self, tier: str) -> str:
        return (
            self._settings.vertex_model_pro
            if tier == ModelTier.PRO
            else self._settings.vertex_model_flash
        )

    @retry(
        retry=retry_if_exception_type(UpstreamError),
        wait=wait_exponential(multiplier=2.0, min=2.0, max=30.0),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    async def generate_structured(
        self,
        *,
        tier: str,
        system: str,
        user: str,
        schema_type: type[T],
    ) -> T:
        self._ensure_init()
        from vertexai.generative_models import GenerationConfig, GenerativeModel

        model = GenerativeModel(self._model_id(tier), system_instruction=system)
        config = GenerationConfig(
            temperature=0.2,
            max_output_tokens=2048,
            response_mime_type="application/json",
        )

        try:
            response = await model.generate_content_async(user, generation_config=config)
        except Exception as exc:  # noqa: BLE001 — vertexai exceptions vary
            logger.warning("vertex.generate_failed", tier=tier, error=str(exc))
            raise UpstreamError("Vertex AI request failed.") from exc

        text = (response.text or "").strip()
        if not text:
            raise UpstreamError("Vertex AI returned an empty response.")

        try:
            return schema_type.model_validate_json(text)
        except PydValidationError as exc:
            logger.warning(
                "vertex.invalid_json", tier=tier, raw=text[:500], error=str(exc)
            )
            # Bubble up as an upstream error — retry decorator will give it
            # one more shot.
            raise UpstreamError("Model returned malformed JSON.") from exc


# ---------- factory ---------------------------------------------------------

_default_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Return the process-wide LLM client (Vertex by default)."""
    global _default_client
    if _default_client is None:
        _default_client = VertexLLMClient()
    return _default_client


def set_llm_client(client: LLMClient) -> None:
    """Inject a different client (used by tests)."""
    global _default_client
    _default_client = client

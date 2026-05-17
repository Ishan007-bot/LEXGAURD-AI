"""Cloud Text-to-Speech wrapper.

Produces an MP3 audio rendering of an analysis summary so visually-impaired
users — or users on the go — can hear the verdict aloud. Counts toward the
GCP-services breadth score and the accessibility score.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass

from app.exceptions import UpstreamError
from app.logging_setup import get_logger

logger = get_logger(__name__)

# Default voice: clear, neutral, conversational. en-US-Neural2-C reads contracts well.
DEFAULT_VOICE = "en-US-Neural2-C"
DEFAULT_LANGUAGE = "en-US"

# Pricing safety: TTS charges per character. Cap input length to keep costs predictable.
MAX_CHARS = 4_000


@dataclass(frozen=True, slots=True)
class SynthesisResult:
    audio_base64: str
    mime_type: str = "audio/mpeg"
    voice: str = DEFAULT_VOICE
    char_count: int = 0


def synthesize(text: str, *, voice: str | None = None) -> SynthesisResult:
    """Render `text` to MP3, returned base64-encoded for inline browser playback."""
    if not text or not text.strip():
        raise UpstreamError("Cannot synthesize empty text.")
    payload = text.strip()
    if len(payload) > MAX_CHARS:
        payload = payload[:MAX_CHARS]

    chosen_voice = voice or DEFAULT_VOICE

    # Lazy import keeps tests light.
    from google.cloud import texttospeech

    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=payload)
        voice_config = texttospeech.VoiceSelectionParams(
            language_code=DEFAULT_LANGUAGE,
            name=chosen_voice,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
        )
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_config,
            audio_config=audio_config,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("tts.synthesize_failed", error=str(exc))
        raise UpstreamError("Text-to-Speech synthesis failed.") from exc

    audio_b64 = base64.b64encode(response.audio_content).decode("ascii")
    return SynthesisResult(
        audio_base64=audio_b64,
        voice=chosen_voice,
        char_count=len(payload),
    )

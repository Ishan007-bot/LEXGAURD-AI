"""Schemas for the TTS endpoint."""

from __future__ import annotations

from pydantic import BaseModel


class TtsResponse(BaseModel):
    audio_base64: str
    mime_type: str
    voice: str
    char_count: int

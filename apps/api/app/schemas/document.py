"""Pydantic request/response schemas for the documents API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.models import (
    ClauseCategory,
    DocumentSource,
    DocumentStatus,
    DocumentType,
)

MAX_PASTE_CHARS = 100_000  # ~30 pages of dense legal text
MAX_URL_LENGTH = 2048


# ---------- requests ---------------------------------------------------------


class CreateFromUploadRequest(BaseModel):
    """Called after the browser successfully PUTs to the signed URL."""

    document_id: str = Field(min_length=1, max_length=64)
    gcs_object: str = Field(min_length=1, max_length=512)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=128)
    size_bytes: int = Field(gt=0)


class CreateFromTextRequest(BaseModel):
    text: str = Field(min_length=20, max_length=MAX_PASTE_CHARS)
    document_type: DocumentType = DocumentType.OTHER
    title: str | None = Field(default=None, max_length=255)


class CreateFromUrlRequest(BaseModel):
    url: HttpUrl
    document_type: DocumentType = DocumentType.TERMS_OF_SERVICE


# ---------- responses --------------------------------------------------------


class ClauseDTO(BaseModel):
    id: str
    index: int
    text: str
    category: ClauseCategory
    start_offset: int
    end_offset: int


class DocumentDTO(BaseModel):
    id: str
    user_id: str
    source: DocumentSource
    status: DocumentStatus
    document_type: DocumentType
    filename: str | None
    content_type: str | None
    size_bytes: int | None
    source_url: str | None
    clause_count: int
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime


class DocumentWithClausesDTO(DocumentDTO):
    clauses: list[ClauseDTO]


class DocumentListResponse(BaseModel):
    items: list[DocumentDTO]
    next_cursor: str | None = None

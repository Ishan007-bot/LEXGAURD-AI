"""Internal domain models (decoupled from API schemas and storage).

Using Pydantic gives us validation + easy Firestore-dict conversion via
`model_dump()` / `model_validate()` without leaking framework types into
the rest of the code.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DocumentSource(StrEnum):
    UPLOAD = "upload"
    PASTED_TEXT = "pasted_text"
    URL = "url"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentType(StrEnum):
    CONTRACT = "contract"
    OFFER_LETTER = "offer_letter"
    QUOTATION = "quotation"
    TICKET_TERMS = "ticket_terms"
    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_SERVICE = "terms_of_service"
    OTHER = "other"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @property
    def numeric(self) -> int:
        """Order severities for comparison: higher = worse."""
        return {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}[self.value]


class AgentName(StrEnum):
    EXTRACTOR = "extractor"
    PROSECUTOR = "prosecutor"
    DEFENDER = "defender"
    JUDGE = "judge"
    NEGOTIATOR = "negotiator"


class ClauseCategory(StrEnum):
    LIABILITY = "liability"
    INDEMNITY = "indemnity"
    TERMINATION = "termination"
    PAYMENT = "payment"
    IP_ASSIGNMENT = "ip_assignment"
    NON_COMPETE = "non_compete"
    NON_SOLICIT = "non_solicit"
    ARBITRATION = "arbitration"
    JURISDICTION = "jurisdiction"
    DATA_PRIVACY = "data_privacy"
    CONFIDENTIALITY = "confidentiality"
    AUTO_RENEWAL = "auto_renewal"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    FORCE_MAJEURE = "force_majeure"
    OTHER = "other"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Clause(BaseModel):
    """A single segmented clause."""

    model_config = ConfigDict(frozen=False)

    id: str
    index: int = Field(ge=0)
    text: str
    category: ClauseCategory = ClauseCategory.OTHER
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)


class Document(BaseModel):
    """A document the user wants analyzed."""

    id: str
    user_id: str
    source: DocumentSource
    status: DocumentStatus = DocumentStatus.PENDING
    document_type: DocumentType = DocumentType.OTHER

    filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    gcs_object: str | None = None
    source_url: str | None = None

    raw_text: str | None = None
    redacted_text: str | None = None
    clauses: list[Clause] = Field(default_factory=list)

    failure_reason: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    def touch(self) -> None:
        self.updated_at = _utcnow()


# ---------- analysis (Phase 3) ----------------------------------------------


class AgentTurn(BaseModel):
    """One agent's contribution to a clause's adversarial debate."""

    agent: AgentName
    argument: str
    citations: list[str] = Field(default_factory=list)
    model: str | None = None  # e.g. "gemini-2.5-flash"


class ClauseAnalysis(BaseModel):
    clause_id: str
    severity: Severity
    risk_score: int = Field(ge=0, le=100)
    plain_english: str
    debate: list[AgentTurn] = Field(default_factory=list)
    suggested_redline: str | None = None
    citations: list[str] = Field(default_factory=list)


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    READY = "ready"
    FAILED = "failed"


class DocumentAnalysis(BaseModel):
    id: str
    document_id: str
    user_id: str
    status: AnalysisStatus = AnalysisStatus.PENDING
    overall_risk_score: int = Field(ge=0, le=100, default=0)
    summary: str = ""
    clauses: list[ClauseAnalysis] = Field(default_factory=list)
    failure_reason: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    def touch(self) -> None:
        self.updated_at = _utcnow()

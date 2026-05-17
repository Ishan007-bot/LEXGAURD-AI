"""Pydantic request/response schemas for analyses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models import AgentName, AnalysisStatus, Severity


class AgentTurnDTO(BaseModel):
    agent: AgentName
    argument: str
    citations: list[str] = []


class ClauseAnalysisDTO(BaseModel):
    clause_id: str
    severity: Severity
    risk_score: int
    plain_english: str
    debate: list[AgentTurnDTO]
    suggested_redline: str | None = None
    citations: list[str] = []


class DocumentAnalysisDTO(BaseModel):
    id: str
    document_id: str
    user_id: str
    status: AnalysisStatus
    overall_risk_score: int
    summary: str
    clauses: list[ClauseAnalysisDTO]
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class AnalysisListResponse(BaseModel):
    items: list[DocumentAnalysisDTO]

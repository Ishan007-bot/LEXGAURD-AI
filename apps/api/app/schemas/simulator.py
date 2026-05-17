"""Schemas for the What-If simulator endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models import Severity


class SimulateRequest(BaseModel):
    scenario: str = Field(min_length=4, max_length=500)


class SimulateResponse(BaseModel):
    headline: str
    consequences: list[str]
    severity: Severity
    advice: str

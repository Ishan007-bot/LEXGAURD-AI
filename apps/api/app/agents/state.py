"""State shape passed between agents in the per-clause LangGraph.

The same object is mutated as it flows through the graph; downstream agents
read the upstream agents' outputs.
"""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, Field

from app.models import (
    AgentName,
    AgentTurn,
    Clause,
    ClauseAnalysis,
    DocumentType,
    Severity,
)


class ProsecutorOutput(BaseModel):
    """Schema the Prosecutor agent must return."""

    preliminary_severity: Severity
    argument: str = Field(min_length=20)
    concerns: list[str] = Field(default_factory=list)


class DefenderOutput(BaseModel):
    """Schema the Defender agent must return."""

    argument: str = Field(min_length=20)
    industry_references: list[str] = Field(default_factory=list)


class JudgeOutput(BaseModel):
    """Schema the Judge agent must return."""

    severity: Severity
    risk_score: int = Field(ge=0, le=100)
    plain_english: str = Field(min_length=10)
    reasoning: str = Field(min_length=20)
    citations: list[str] = Field(default_factory=list)


class NegotiatorOutput(BaseModel):
    """Schema the Negotiator agent must return."""

    suggested_redline: str = Field(min_length=10)
    plain_english_explanation: str = Field(min_length=10)
    walk_away: bool = False


class ScenarioOutput(BaseModel):
    """Schema the Scenario Simulator must return."""

    headline: str = Field(min_length=4, max_length=240)
    consequences: list[str] = Field(min_length=1, max_length=5)
    severity: Severity
    advice: str = Field(min_length=4, max_length=300)


# ---------- LangGraph state -------------------------------------------------


class ClauseState(TypedDict, total=False):
    """The mutable state that flows through the per-clause graph.

    TypedDict (not Pydantic) because LangGraph natively understands it and
    cheaply merges partial updates returned by nodes.
    """

    # Inputs (always present)
    clause: Clause
    document_type: DocumentType

    # Agent outputs (filled in as nodes execute)
    prosecutor: ProsecutorOutput
    defender: DefenderOutput
    judge: JudgeOutput
    negotiator: NegotiatorOutput

    # Routing hint set by the analyzer: should the Judge use Pro?
    use_pro_judge: bool


# ---------- helpers ---------------------------------------------------------


def to_clause_analysis(state: ClauseState) -> ClauseAnalysis:
    """Collapse a finished `ClauseState` into a `ClauseAnalysis`."""
    clause: Clause = state["clause"]
    judge = state["judge"]
    debate: list[AgentTurn] = []

    if (prosecutor := state.get("prosecutor")) is not None:
        debate.append(
            AgentTurn(
                agent=AgentName.PROSECUTOR,
                argument=prosecutor.argument,
                citations=prosecutor.concerns,
            )
        )
    if (defender := state.get("defender")) is not None:
        debate.append(
            AgentTurn(
                agent=AgentName.DEFENDER,
                argument=defender.argument,
                citations=defender.industry_references,
            )
        )
    debate.append(
        AgentTurn(
            agent=AgentName.JUDGE,
            argument=judge.reasoning,
            citations=judge.citations,
        )
    )
    if (negotiator := state.get("negotiator")) is not None:
        debate.append(
            AgentTurn(
                agent=AgentName.NEGOTIATOR,
                argument=negotiator.plain_english_explanation,
            )
        )

    return ClauseAnalysis(
        clause_id=clause.id,
        severity=judge.severity,
        risk_score=judge.risk_score,
        plain_english=judge.plain_english,
        debate=debate,
        suggested_redline=(negotiator.suggested_redline if negotiator else None),
        citations=list(judge.citations),
    )


__all__ = [
    "ProsecutorOutput",
    "DefenderOutput",
    "JudgeOutput",
    "NegotiatorOutput",
    "ScenarioOutput",
    "ClauseState",
    "to_clause_analysis",
]

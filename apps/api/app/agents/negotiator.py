"""Negotiator agent — produces a concrete redline + plain-English rationale.

Skipped automatically for clauses the Judge marks Low or Info (no point
negotiating something that isn't actually risky — saves tokens).
"""

from __future__ import annotations

from app.agents.prompts import SYSTEM_NEGOTIATOR, negotiator_user_prompt
from app.agents.state import ClauseState, NegotiatorOutput
from app.models import Severity
from app.services.vertex import LLMClient, ModelTier


def should_negotiate(state: ClauseState) -> bool:
    judge = state.get("judge")
    if judge is None:
        return False
    return judge.severity.numeric >= Severity.MEDIUM.numeric


async def run_negotiator(state: ClauseState, *, client: LLMClient) -> dict[str, NegotiatorOutput]:
    clause = state["clause"]
    judge = state["judge"]
    output = await client.generate_structured(
        tier=ModelTier.FLASH,
        system=SYSTEM_NEGOTIATOR,
        user=negotiator_user_prompt(
            clause_text=clause.text,
            plain_english=judge.plain_english,
            severity=judge.severity.value,
        ),
        schema_type=NegotiatorOutput,
    )
    return {"negotiator": output}

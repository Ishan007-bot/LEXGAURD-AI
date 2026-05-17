"""Defender agent — argues the clause is standard / industry-normal."""

from __future__ import annotations

from app.agents.prompts import SYSTEM_DEFENDER, defender_user_prompt
from app.agents.state import ClauseState, DefenderOutput
from app.services.vertex import LLMClient, ModelTier


async def run_defender(state: ClauseState, *, client: LLMClient) -> dict[str, DefenderOutput]:
    clause = state["clause"]
    prosecutor = state["prosecutor"]
    output = await client.generate_structured(
        tier=ModelTier.FLASH,
        system=SYSTEM_DEFENDER,
        user=defender_user_prompt(
            document_type=state["document_type"].value,
            clause_text=clause.text,
            prosecutor_argument=prosecutor.argument,
        ),
        schema_type=DefenderOutput,
    )
    return {"defender": output}

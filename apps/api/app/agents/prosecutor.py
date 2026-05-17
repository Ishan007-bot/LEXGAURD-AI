"""Prosecutor agent — argues the clause is harmful to the signer."""

from __future__ import annotations

from app.agents.prompts import SYSTEM_PROSECUTOR, prosecutor_user_prompt
from app.agents.state import ClauseState, ProsecutorOutput
from app.services.vertex import LLMClient, ModelTier


async def run_prosecutor(state: ClauseState, *, client: LLMClient) -> dict[str, ProsecutorOutput]:
    clause = state["clause"]
    output = await client.generate_structured(
        tier=ModelTier.FLASH,
        system=SYSTEM_PROSECUTOR,
        user=prosecutor_user_prompt(
            document_type=state["document_type"].value,
            clause_text=clause.text,
        ),
        schema_type=ProsecutorOutput,
    )
    return {"prosecutor": output}

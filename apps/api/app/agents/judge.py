"""Judge agent — weighs both sides, assigns severity + 0-100 risk score.

Routing: by default the Judge uses Gemini Flash. The analyzer flips
`state["use_pro_judge"] = True` on the top-N most concerning clauses
(per Prosecutor severity) to escalate them to Gemini Pro. See docs/budget.md.
"""

from __future__ import annotations

from app.agents.prompts import SYSTEM_JUDGE, judge_user_prompt
from app.agents.state import ClauseState, JudgeOutput
from app.services.vertex import LLMClient, ModelTier


async def run_judge(state: ClauseState, *, client: LLMClient) -> dict[str, JudgeOutput]:
    clause = state["clause"]
    prosecutor = state["prosecutor"]
    defender = state["defender"]
    tier = ModelTier.PRO if state.get("use_pro_judge") else ModelTier.FLASH

    output = await client.generate_structured(
        tier=tier,
        system=SYSTEM_JUDGE,
        user=judge_user_prompt(
            document_type=state["document_type"].value,
            clause_text=clause.text,
            prosecutor_argument=prosecutor.argument,
            defender_argument=defender.argument,
        ),
        schema_type=JudgeOutput,
    )
    return {"judge": output}

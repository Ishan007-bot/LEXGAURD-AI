"""Scenario simulator agent.

Given a stored `DocumentAnalysis` and a real-world scenario the user is worried
about, this agent picks the clauses most relevant to the scenario and predicts
the concrete consequences. Uses Gemini Flash — one call per scenario, cheap.
"""

from __future__ import annotations

from app.agents.prompts import SYSTEM_SIMULATOR, simulator_user_prompt
from app.agents.state import ScenarioOutput
from app.models import Clause, DocumentType
from app.services.vertex import LLMClient, ModelTier


def _build_clauses_block(clauses: list[Clause]) -> str:
    """Format the clause list for the prompt — keep it short, the model has limits."""
    lines: list[str] = []
    for c in clauses:
        snippet = c.text if len(c.text) <= 500 else c.text[:500] + "…"
        lines.append(f"Clause #{c.index + 1} ({c.category.value}):\n{snippet}")
    return "\n\n".join(lines)


async def run_scenario(
    *,
    client: LLMClient,
    document_type: DocumentType,
    clauses: list[Clause],
    scenario: str,
) -> ScenarioOutput:
    """One Flash call per scenario."""
    return await client.generate_structured(
        tier=ModelTier.FLASH,
        system=SYSTEM_SIMULATOR,
        user=simulator_user_prompt(
            document_type=document_type.value,
            scenario=scenario,
            clauses_block=_build_clauses_block(clauses),
        ),
        schema_type=ScenarioOutput,
    )

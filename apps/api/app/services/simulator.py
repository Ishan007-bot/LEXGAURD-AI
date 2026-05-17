"""Service that runs a what-if scenario against a stored analysis."""

from __future__ import annotations

from app.agents.scenarios import run_scenario
from app.agents.state import ScenarioOutput
from app.exceptions import NotFoundError, ValidationError
from app.repositories.analyses import (
    AnalysisRepository,
    FirestoreAnalysisRepository,
)
from app.repositories.documents import (
    DocumentRepository,
    FirestoreDocumentRepository,
)
from app.services.vertex import LLMClient, get_llm_client

MAX_SCENARIO_LEN = 500
MAX_CLAUSES_TO_INCLUDE = 12


async def simulate(
    *,
    analysis_id: str,
    user_id: str,
    scenario: str,
    document_repo: DocumentRepository | None = None,
    analysis_repo: AnalysisRepository | None = None,
    llm_client: LLMClient | None = None,
) -> ScenarioOutput:
    if not scenario or not scenario.strip():
        raise ValidationError("Scenario is empty.")
    if len(scenario) > MAX_SCENARIO_LEN:
        raise ValidationError(
            f"Scenario is too long ({len(scenario)} chars; max {MAX_SCENARIO_LEN}).",
        )

    a_repo = analysis_repo or FirestoreAnalysisRepository()
    d_repo = document_repo or FirestoreDocumentRepository()
    client = llm_client or get_llm_client()

    analysis = a_repo.get(analysis_id=analysis_id, user_id=user_id)
    document = d_repo.get(document_id=analysis.document_id, user_id=user_id)
    if not document.clauses:
        raise NotFoundError("Document has no clauses to simulate against.")

    # Pick the top-N most severe clauses — keeps the prompt cheap and focused.
    ordered = sorted(
        analysis.clauses,
        key=lambda c: c.severity.numeric,
        reverse=True,
    )
    keep_ids = {c.clause_id for c in ordered[:MAX_CLAUSES_TO_INCLUDE]}
    relevant = [c for c in document.clauses if c.id in keep_ids]

    return await run_scenario(
        client=client,
        document_type=document.document_type,
        clauses=relevant,
        scenario=scenario.strip(),
    )

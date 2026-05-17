"""Document analysis orchestrator.

Coordinates the per-clause LangGraph runs with bounded concurrency, applies
the cost-saving routing (Pro Judge only on top-3 risky clauses), and writes
the final `DocumentAnalysis` to Firestore.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING

from app.agents.graph import build_clause_graph
from app.agents.state import (
    ClauseState,
    ProsecutorOutput,
    to_clause_analysis,
)
from app.config import get_settings
from app.exceptions import LexGuardError, ValidationError
from app.logging_setup import get_logger
from app.models import (
    AnalysisStatus,
    Clause,
    ClauseAnalysis,
    Document,
    DocumentAnalysis,
    DocumentStatus,
    Severity,
)
from app.repositories.analyses import (
    AnalysisRepository,
    FirestoreAnalysisRepository,
)
from app.repositories.documents import (
    DocumentRepository,
    FirestoreDocumentRepository,
)
from app.services.vertex import LLMClient, ModelTier, get_llm_client

if TYPE_CHECKING:  # pragma: no cover
    pass

logger = get_logger(__name__)

PRO_JUDGE_TOP_N = 3
MAX_CLAUSES_PER_DOC = 60
# Vertex AI new-project quotas are tight (~5 RPM for Pro, ~60 RPM for Flash).
# Keeping concurrency at 1 sequentialises the calls so we don't trigger 429s.
# tenacity will retry any 429 that still slips through.
PROSECUTOR_CONCURRENCY = 1
GRAPH_CONCURRENCY = 1


# ---------------------------------------------------------------------------


async def _run_prosecutor_pass(
    document: Document, client: LLMClient
) -> dict[str, ProsecutorOutput]:
    """Run only the Prosecutor on every clause to get preliminary severities."""
    from app.agents.prompts import SYSTEM_PROSECUTOR, prosecutor_user_prompt

    semaphore = asyncio.Semaphore(PROSECUTOR_CONCURRENCY)
    results: dict[str, ProsecutorOutput] = {}

    async def _one(clause: Clause) -> None:
        async with semaphore:
            output = await client.generate_structured(
                tier=ModelTier.FLASH,
                system=SYSTEM_PROSECUTOR,
                user=prosecutor_user_prompt(
                    document_type=document.document_type.value,
                    clause_text=clause.text,
                ),
                schema_type=ProsecutorOutput,
            )
            results[clause.id] = output

    await asyncio.gather(*(_one(c) for c in document.clauses))
    return results


def _select_pro_judge_clause_ids(
    prosecutor_outputs: dict[str, ProsecutorOutput],
) -> set[str]:
    """Top-N clauses by Prosecutor's preliminary severity (ties broken by order)."""
    ranked = sorted(
        prosecutor_outputs.items(),
        key=lambda kv: kv[1].preliminary_severity.numeric,
        reverse=True,
    )
    return {clause_id for clause_id, _ in ranked[:PRO_JUDGE_TOP_N]}


async def _run_graph_for_clause(
    clause: Clause,
    document: Document,
    prosecutor_output: ProsecutorOutput,
    use_pro_judge: bool,
    graph,
    semaphore: asyncio.Semaphore,
) -> ClauseAnalysis:
    initial: ClauseState = {
        "clause": clause,
        "document_type": document.document_type,
        "prosecutor": prosecutor_output,
        "use_pro_judge": use_pro_judge,
    }
    async with semaphore:
        # LangGraph re-runs the prosecutor node by default; we pre-fill its
        # output and the graph node will simply overwrite it from cache below.
        # To save the duplicate Vertex call we start the graph from the
        # "defender" node by hand: invoke each node manually.
        from app.agents.defender import run_defender
        from app.agents.judge import run_judge
        from app.agents.negotiator import run_negotiator, should_negotiate

        state: ClauseState = initial
        state.update(await run_defender(state, client=get_llm_client()))
        state.update(await run_judge(state, client=get_llm_client()))
        if should_negotiate(state):
            state.update(await run_negotiator(state, client=get_llm_client()))
        _ = graph  # graph kept for callers that want to use it directly
    return to_clause_analysis(state)


def _overall_score(clauses: list[ClauseAnalysis]) -> int:
    if not clauses:
        return 0
    # Weighted by severity squared so a single critical clause moves the needle.
    weights = {s: s.numeric**2 for s in Severity}
    weighted = sum(c.risk_score * weights[c.severity] for c in clauses)
    denom = sum(weights[c.severity] for c in clauses) or 1
    return min(100, max(0, round(weighted / denom)))


def _summary(clauses: list[ClauseAnalysis], overall: int) -> str:
    if not clauses:
        return "No clauses were extracted from this document."
    critical = sum(1 for c in clauses if c.severity is Severity.CRITICAL)
    high = sum(1 for c in clauses if c.severity is Severity.HIGH)
    medium = sum(1 for c in clauses if c.severity is Severity.MEDIUM)
    parts = [f"Overall risk score: {overall}/100."]
    if critical:
        parts.append(f"{critical} critical concern(s) — do not sign without changes.")
    elif high:
        parts.append(f"{high} high-risk clause(s) — review carefully.")
    elif medium:
        parts.append(f"{medium} medium-risk clause(s) — minor concerns.")
    else:
        parts.append("No serious concerns detected.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def analyze_document(
    *,
    document_id: str,
    user_id: str,
    document_repo: DocumentRepository | None = None,
    analysis_repo: AnalysisRepository | None = None,
    llm_client: LLMClient | None = None,
) -> DocumentAnalysis:
    """Run the full adversarial analysis on a previously-processed document."""
    doc_repo = document_repo or FirestoreDocumentRepository()
    analy_repo = analysis_repo or FirestoreAnalysisRepository()
    client = llm_client or get_llm_client()

    document = doc_repo.get(document_id=document_id, user_id=user_id)
    if document.status is not DocumentStatus.READY:
        raise ValidationError(
            f"Document is not ready for analysis (status={document.status.value})."
        )
    if not document.clauses:
        raise ValidationError("Document has no clauses to analyze.")
    if len(document.clauses) > MAX_CLAUSES_PER_DOC:
        raise ValidationError(
            f"Document has {len(document.clauses)} clauses; limit is {MAX_CLAUSES_PER_DOC}."
        )

    analysis = DocumentAnalysis(
        id=uuid.uuid4().hex,
        document_id=document.id,
        user_id=user_id,
        status=AnalysisStatus.RUNNING,
    )
    analy_repo.save(analysis)

    try:
        # 1. Prosecutor pass (Flash, cheap) — gives us severity priors.
        prosecutor_outputs = await _run_prosecutor_pass(document, client)

        # 2. Pick top-N clauses for the Pro-Judge escalation.
        pro_judge_ids = _select_pro_judge_clause_ids(prosecutor_outputs)

        # 3. Run Defender → Judge → (Negotiator) for each clause in parallel.
        graph = build_clause_graph(client)
        semaphore = asyncio.Semaphore(GRAPH_CONCURRENCY)

        async def _per_clause(clause: Clause) -> ClauseAnalysis:
            return await _run_graph_for_clause(
                clause=clause,
                document=document,
                prosecutor_output=prosecutor_outputs[clause.id],
                use_pro_judge=clause.id in pro_judge_ids,
                graph=graph,
                semaphore=semaphore,
            )

        results: list[ClauseAnalysis] = await asyncio.gather(
            *(_per_clause(c) for c in document.clauses)
        )

        overall = _overall_score(results)
        analysis.clauses = results
        analysis.overall_risk_score = overall
        analysis.summary = _summary(results, overall)
        analysis.status = AnalysisStatus.READY
        analy_repo.save(analysis)
        logger.info(
            "analysis.complete",
            analysis_id=analysis.id,
            document_id=document.id,
            overall=overall,
            clause_count=len(results),
            pro_judge=list(pro_judge_ids),
        )
        return analysis

    except LexGuardError as exc:
        analysis.status = AnalysisStatus.FAILED
        analysis.failure_reason = exc.message
        analy_repo.save(analysis)
        raise
    except Exception as exc:  # noqa: BLE001 — defensive
        analysis.status = AnalysisStatus.FAILED
        analysis.failure_reason = str(exc)
        analy_repo.save(analysis)
        logger.exception("analysis.unexpected_failure", error=str(exc))
        raise

"""HTTP routes for adversarial analyses."""

from fastapi import APIRouter, Depends, Request

from app.auth import AuthenticatedUser, require_user
from app.middleware.rate_limit import limiter
from app.models import DocumentAnalysis
from app.repositories.analyses import FirestoreAnalysisRepository
from app.schemas.analysis import (
    AgentTurnDTO,
    AnalysisListResponse,
    ClauseAnalysisDTO,
    DocumentAnalysisDTO,
)
from app.services import analyzer

router = APIRouter(tags=["analyses"])


def _to_dto(a: DocumentAnalysis) -> DocumentAnalysisDTO:
    return DocumentAnalysisDTO(
        id=a.id,
        document_id=a.document_id,
        user_id=a.user_id,
        status=a.status,
        overall_risk_score=a.overall_risk_score,
        summary=a.summary,
        clauses=[
            ClauseAnalysisDTO(
                clause_id=c.clause_id,
                severity=c.severity,
                risk_score=c.risk_score,
                plain_english=c.plain_english,
                debate=[
                    AgentTurnDTO(agent=t.agent, argument=t.argument, citations=t.citations)
                    for t in c.debate
                ],
                suggested_redline=c.suggested_redline,
                citations=c.citations,
            )
            for c in a.clauses
        ],
        failure_reason=a.failure_reason,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.post(
    "/documents/{document_id}/analyses",
    response_model=DocumentAnalysisDTO,
    status_code=201,
)
@limiter.limit("5/minute")
async def create_analysis(
    request: Request,
    document_id: str,
    user: AuthenticatedUser = Depends(require_user),
) -> DocumentAnalysisDTO:
    """Run the full multi-agent analysis on a previously-processed document."""
    analysis = await analyzer.analyze_document(document_id=document_id, user_id=user.uid)
    return _to_dto(analysis)


@router.get("/analyses/{analysis_id}", response_model=DocumentAnalysisDTO)
async def get_analysis(
    analysis_id: str,
    user: AuthenticatedUser = Depends(require_user),
) -> DocumentAnalysisDTO:
    repo = FirestoreAnalysisRepository()
    return _to_dto(repo.get(analysis_id=analysis_id, user_id=user.uid))


@router.get(
    "/documents/{document_id}/analyses",
    response_model=AnalysisListResponse,
)
async def list_analyses(
    document_id: str,
    user: AuthenticatedUser = Depends(require_user),
) -> AnalysisListResponse:
    repo = FirestoreAnalysisRepository()
    analyses = repo.list_for_document(document_id=document_id, user_id=user.uid)
    return AnalysisListResponse(items=[_to_dto(a) for a in analyses])

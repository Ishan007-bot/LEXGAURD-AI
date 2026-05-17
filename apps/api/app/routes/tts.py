"""HTTP route for Text-to-Speech voice walkthrough."""

from fastapi import APIRouter, Depends, Request

from app.auth import AuthenticatedUser, require_user
from app.middleware.rate_limit import limiter
from app.repositories.analyses import FirestoreAnalysisRepository
from app.schemas.tts import TtsResponse
from app.services.tts import synthesize

router = APIRouter(tags=["tts"])


def _build_walkthrough_text(summary: str, headline_clauses: list[str]) -> str:
    """Compose the spoken script from analysis content."""
    intro = "LexGuard verdict. " + summary.rstrip(".") + "."
    if headline_clauses:
        intro += " The most concerning clauses are: " + "; ".join(headline_clauses) + "."
    intro += " Please review the detailed transcript on screen before signing."
    return intro


@router.post(
    "/analyses/{analysis_id}/tts",
    response_model=TtsResponse,
    status_code=200,
)
@limiter.limit("10/minute")
async def analysis_tts(
    request: Request,
    analysis_id: str,
    user: AuthenticatedUser = Depends(require_user),
) -> TtsResponse:
    """Synthesize a spoken walkthrough of the analysis summary."""
    repo = FirestoreAnalysisRepository()
    analysis = repo.get(analysis_id=analysis_id, user_id=user.uid)

    top = [c for c in analysis.clauses if c.severity.numeric >= 3][:3]
    headline_clauses = [c.plain_english for c in top]
    text = _build_walkthrough_text(analysis.summary, headline_clauses)

    result = synthesize(text)
    return TtsResponse(
        audio_base64=result.audio_base64,
        mime_type=result.mime_type,
        voice=result.voice,
        char_count=result.char_count,
    )

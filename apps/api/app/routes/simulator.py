"""HTTP route for the What-If scenario simulator."""

from fastapi import APIRouter, Depends, Request

from app.auth import AuthenticatedUser, require_user
from app.middleware.rate_limit import limiter
from app.schemas.simulator import SimulateRequest, SimulateResponse
from app.services import simulator

router = APIRouter(tags=["simulator"])


@router.post(
    "/analyses/{analysis_id}/simulate",
    response_model=SimulateResponse,
    status_code=200,
)
@limiter.limit("15/minute")
async def simulate(
    request: Request,
    analysis_id: str,
    payload: SimulateRequest,
    user: AuthenticatedUser = Depends(require_user),
) -> SimulateResponse:
    """Run one what-if scenario against a stored analysis."""
    result = await simulator.simulate(
        analysis_id=analysis_id,
        user_id=user.uid,
        scenario=payload.scenario,
    )
    return SimulateResponse(
        headline=result.headline,
        consequences=result.consequences,
        severity=result.severity,
        advice=result.advice,
    )

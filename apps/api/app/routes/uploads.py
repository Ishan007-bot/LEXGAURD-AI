"""HTTP routes for upload initiation."""

from fastapi import APIRouter, Depends, Request

from app.auth import AuthenticatedUser, require_user
from app.middleware.rate_limit import limiter
from app.schemas.upload import UploadInitRequest, UploadInitResponse
from app.services.uploads import init_upload as svc_init_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/init", response_model=UploadInitResponse, status_code=201)
@limiter.limit("10/minute")
async def init_upload(
    request: Request,
    payload: UploadInitRequest,
    user: AuthenticatedUser = Depends(require_user),
) -> UploadInitResponse:
    """Allocate a document id and return a signed PUT URL.

    The browser then PUTs the file directly to GCS — the API never touches it.
    """
    return svc_init_upload(payload, user_id=user.uid)

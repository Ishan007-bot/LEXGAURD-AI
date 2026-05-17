"""HTTP routes for document creation, retrieval, and listing."""

from fastapi import APIRouter, Depends, Query, Request

from app.auth import AuthenticatedUser, require_user
from app.middleware.rate_limit import limiter
from app.models import Document
from app.repositories.documents import FirestoreDocumentRepository
from app.schemas.document import (
    ClauseDTO,
    CreateFromTextRequest,
    CreateFromUploadRequest,
    CreateFromUrlRequest,
    DocumentDTO,
    DocumentListResponse,
    DocumentWithClausesDTO,
)
from app.services import pipeline

router = APIRouter(prefix="/documents", tags=["documents"])


def _summary(d: Document) -> DocumentDTO:
    return DocumentDTO(
        id=d.id,
        user_id=d.user_id,
        source=d.source,
        status=d.status,
        document_type=d.document_type,
        filename=d.filename,
        content_type=d.content_type,
        size_bytes=d.size_bytes,
        source_url=d.source_url,
        clause_count=len(d.clauses),
        failure_reason=d.failure_reason,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


def _detailed(d: Document) -> DocumentWithClausesDTO:
    return DocumentWithClausesDTO(
        **_summary(d).model_dump(),
        clauses=[
            ClauseDTO(
                id=c.id,
                index=c.index,
                text=c.text,
                category=c.category,
                start_offset=c.start_offset,
                end_offset=c.end_offset,
            )
            for c in d.clauses
        ],
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@router.post("/from-upload", response_model=DocumentWithClausesDTO, status_code=201)
@limiter.limit("20/minute")
async def create_from_upload(
    request: Request,
    payload: CreateFromUploadRequest,
    user: AuthenticatedUser = Depends(require_user),
) -> DocumentWithClausesDTO:
    doc = pipeline.process_uploaded_document(
        document_id=payload.document_id,
        user_id=user.uid,
        gcs_object=payload.gcs_object,
        filename=payload.filename,
        content_type=payload.content_type,
        size_bytes=payload.size_bytes,
    )
    return _detailed(doc)


@router.post("/from-text", response_model=DocumentWithClausesDTO, status_code=201)
@limiter.limit("20/minute")
async def create_from_text(
    request: Request,
    payload: CreateFromTextRequest,
    user: AuthenticatedUser = Depends(require_user),
) -> DocumentWithClausesDTO:
    doc = pipeline.process_pasted_text(
        user_id=user.uid,
        text=payload.text,
        document_type=payload.document_type,
        title=payload.title,
    )
    return _detailed(doc)


@router.post("/from-url", response_model=DocumentWithClausesDTO, status_code=201)
@limiter.limit("10/minute")
async def create_from_url(
    request: Request,
    payload: CreateFromUrlRequest,
    user: AuthenticatedUser = Depends(require_user),
) -> DocumentWithClausesDTO:
    doc = await pipeline.process_url(
        user_id=user.uid,
        url=str(payload.url),
        document_type=payload.document_type,
    )
    return _detailed(doc)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


@router.get("/{document_id}", response_model=DocumentWithClausesDTO)
async def get_document(
    document_id: str,
    user: AuthenticatedUser = Depends(require_user),
) -> DocumentWithClausesDTO:
    repo = FirestoreDocumentRepository()
    doc = repo.get(document_id=document_id, user_id=user.uid)
    return _detailed(doc)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    user: AuthenticatedUser = Depends(require_user),
    limit: int = Query(default=20, ge=1, le=100),
) -> DocumentListResponse:
    repo = FirestoreDocumentRepository()
    docs = repo.list_for_user(user_id=user.uid, limit=limit)
    return DocumentListResponse(items=[_summary(d) for d in docs])

"""Domain exceptions and global FastAPI exception handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging_setup import get_logger

logger = get_logger(__name__)


class LexGuardError(Exception):
    """Base class for application-domain errors."""

    status_code: int = 500
    error_code: str = "lexguard_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(LexGuardError):
    status_code = 400
    error_code = "validation_error"


class AuthenticationError(LexGuardError):
    status_code = 401
    error_code = "unauthenticated"


class AuthorizationError(LexGuardError):
    status_code = 403
    error_code = "forbidden"


class NotFoundError(LexGuardError):
    status_code = 404
    error_code = "not_found"


class RateLimitError(LexGuardError):
    status_code = 429
    error_code = "rate_limited"


class UpstreamError(LexGuardError):
    """An external dependency (Vertex AI, GCS, ...) failed."""

    status_code = 502
    error_code = "upstream_error"


def _error_payload(
    *,
    code: str,
    message: str,
    request_id: str | None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {"code": code, "message": message},
    }
    if request_id:
        payload["error"]["requestId"] = request_id
    if details:
        payload["error"]["details"] = details
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    """Install the exception handlers on the given app."""

    @app.exception_handler(LexGuardError)
    async def _domain(request: Request, exc: LexGuardError) -> ORJSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            "domain_error",
            code=exc.error_code,
            status=exc.status_code,
            message=exc.message,
        )
        return ORJSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                code=exc.error_code,
                message=exc.message,
                request_id=request_id,
                details=exc.details,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException) -> ORJSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return ORJSONResponse(
            status_code=exc.status_code,
            content=_error_payload(
                code="http_error",
                message=str(exc.detail),
                request_id=request_id,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> ORJSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return ORJSONResponse(
            status_code=422,
            content=_error_payload(
                code="validation_error",
                message="Request validation failed.",
                request_id=request_id,
                details={"errors": exc.errors()},
            ),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> ORJSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("unhandled_error", error=str(exc))
        return ORJSONResponse(
            status_code=500,
            content=_error_payload(
                code="internal_error",
                message="An unexpected error occurred.",
                request_id=request_id,
            ),
        )

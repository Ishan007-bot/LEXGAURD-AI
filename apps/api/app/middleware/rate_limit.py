"""Per-IP / per-user rate limiting via SlowAPI."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


def _key_func(request: Request) -> str:
    """Prefer authenticated user id if present, otherwise client IP."""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=_key_func, default_limits=["60/minute"])


def register_rate_limiter(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def _on_rate_limit(request: Request, exc: RateLimitExceeded) -> ORJSONResponse:
        request_id = getattr(request.state, "request_id", None)
        body: dict[str, object] = {
            "error": {
                "code": "rate_limited",
                "message": f"Rate limit exceeded: {exc.detail}",
            }
        }
        if request_id:
            body["error"]["requestId"] = request_id  # type: ignore[index]
        return ORJSONResponse(status_code=429, content=body)

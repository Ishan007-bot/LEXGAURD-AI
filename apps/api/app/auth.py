"""Firebase Auth token verification dependency.

Used as `Depends(require_user)` or `Depends(optional_user)` on routes.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.exceptions import AuthenticationError
from app.logging_setup import get_logger

logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    uid: str
    email: str | None
    name: str | None


async def _verify_token(token: str) -> AuthenticatedUser:
    # Imported lazily so unit tests don't require firebase-admin to be installed.
    from firebase_admin import auth as fb_auth

    from app.clients.gcp import get_firebase_app

    try:
        get_firebase_app()
        decoded = fb_auth.verify_id_token(token, check_revoked=False)
    except Exception as exc:  # noqa: BLE001 — firebase raises many specific types
        logger.warning("auth.verify_failed", error=str(exc))
        raise AuthenticationError("Invalid or expired authentication token.") from exc

    uid = decoded.get("uid") or decoded.get("user_id")
    if not uid:
        raise AuthenticationError("Token missing user identifier.")
    return AuthenticatedUser(
        uid=uid,
        email=decoded.get("email"),
        name=decoded.get("name"),
    )


async def require_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthenticatedUser:
    """Reject any request without a valid Firebase ID token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Missing bearer token.")
    user = await _verify_token(credentials.credentials)
    request.state.user_id = user.uid
    return user


async def optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthenticatedUser | None:
    """Return the user if a valid token is supplied, else None."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    user = await _verify_token(credentials.credentials)
    request.state.user_id = user.uid
    return user

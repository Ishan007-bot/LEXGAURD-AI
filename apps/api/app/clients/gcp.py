"""Lazy, singleton GCP client factories.

Using `lru_cache` keeps construction cost off the import path (important for
Cloud Run cold starts) and gives tests a clean override point via
`get_*.cache_clear()`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from app.config import get_settings

if TYPE_CHECKING:  # pragma: no cover
    from firebase_admin import App as FirebaseApp
    from google.cloud import firestore, storage


@lru_cache(maxsize=1)
def get_firestore_client() -> "firestore.Client":
    from google.cloud import firestore

    settings = get_settings()
    return firestore.Client(
        project=settings.gcp_project_id,
        database=settings.firestore_database,
    )


@lru_cache(maxsize=1)
def get_storage_client() -> "storage.Client":
    from google.cloud import storage

    settings = get_settings()
    return storage.Client(project=settings.gcp_project_id)


@lru_cache(maxsize=1)
def get_firebase_app() -> "FirebaseApp":
    """Initialise the firebase-admin SDK once.

    Uses Application Default Credentials so the same code works locally
    (`gcloud auth application-default login`) and on Cloud Run.
    """
    import firebase_admin
    from firebase_admin import credentials

    if firebase_admin._apps:  # type: ignore[attr-defined]
        return firebase_admin.get_app()

    settings = get_settings()
    return firebase_admin.initialize_app(
        credentials.ApplicationDefault(),
        {"projectId": settings.gcp_project_id},
    )

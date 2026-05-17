"""Lazy-initialised Google Cloud client factories."""

from app.clients.gcp import (
    get_firebase_app,
    get_firestore_client,
    get_storage_client,
)

__all__ = ["get_firebase_app", "get_firestore_client", "get_storage_client"]

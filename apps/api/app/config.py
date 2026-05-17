"""Typed application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    allowed_origins: str = "http://localhost:3000"

    gcp_project_id: str = "lexguard-dev"
    gcp_region: str = "asia-south1"

    vertex_location: str = "us-central1"
    vertex_model_pro: str = "gemini-2.5-pro"
    vertex_model_flash: str = "gemini-2.5-flash"

    firestore_database: str = "(default)"
    firestore_collection_documents: str = "documents"
    firestore_collection_analyses: str = "analyses"

    gcs_upload_bucket: str = "lexguard-uploads"
    gcs_reports_bucket: str = "lexguard-reports"

    docai_processor_id: str = ""
    docai_location: str = "us"

    # In-process cache sizing (Memorystore dropped to fit $5 budget — see docs/budget.md).
    analysis_cache_size: int = 256
    analysis_cache_ttl_seconds: int = 3600

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance."""
    return Settings()  # type: ignore[call-arg]

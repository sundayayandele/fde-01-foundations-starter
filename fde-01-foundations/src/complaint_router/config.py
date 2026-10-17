"""Runtime settings, read from environment variables (and .env for local runs)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore",
                                      protected_namespaces=())

    service_name: str = "fde-01-foundations"
    environment: str = "local"
    log_level: str = "INFO"

    # Where trained model bundles live: <model_dir>/<dataset>/<model>/meta.json
    model_dir: str = "models"
    # Bundle served when a request names none, as "<dataset>/<model>".
    serve_model: str = "banking77/baseline"
    # Below this top-class probability, or with a top-2 margin below route_margin,
    # a prediction is routed to a human instead of being auto-assigned.
    route_threshold: float = 0.5
    route_margin: float = 0.1
    max_text_chars: int = 5000
    max_batch: int = 256

    # Kept from the template for later phases; this repo makes no LLM calls.
    llm_provider: str = "mistral"
    llm_providers_file: str = "config/providers.yaml"
    llm_timeout_seconds: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Application configuration via Pydantic settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .template_setup import ensure_sample_templates


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    api_key: str = Field("dev-secret", validation_alias=AliasChoices("API_KEY", "api_key"))
    database_url: str = Field("sqlite:////tmp/export_jobs.db", validation_alias=AliasChoices("DATABASE_URL", "database_url"))
    redis_url: str = Field("redis://localhost:6379/0", validation_alias=AliasChoices("REDIS_URL", "redis_url"))
    storage_dir: Path = Field(Path("storage"), validation_alias=AliasChoices("STORAGE_DIR", "storage_dir"))
    template_dir: Path = Field(Path("templates"), validation_alias=AliasChoices("TEMPLATE_DIR", "template_dir"))
    assets_dir: Path = Field(Path("templates/assets"), validation_alias=AliasChoices("ASSETS_DIR", "assets_dir"))
    file_ttl_hours: int = Field(24, validation_alias=AliasChoices("FILE_TTL_HOURS", "file_ttl_hours"))
    include_pdf: bool = Field(False, validation_alias=AliasChoices("DEFAULT_INCLUDE_PDF", "include_pdf"))
    enable_zip_default: bool = Field(True, validation_alias=AliasChoices("DEFAULT_ZIP_ALL", "zip_all"))
    allowed_templates: list[str] = Field(default_factory=lambda: [
        "summary_template.docx",
        "full_report_template.docx",
    ])
    celery_task_always_eager: bool = Field(False, validation_alias=AliasChoices("CELERY_TASK_ALWAYS_EAGER", "task_always_eager"))
    celery_broker_url: str | None = Field(None, validation_alias=AliasChoices("CELERY_BROKER_URL", "celery_broker_url"))
    celery_result_backend: str | None = Field(None, validation_alias=AliasChoices("CELERY_RESULT_BACKEND", "celery_result_backend"))

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    config = Settings()
    config.storage_dir.mkdir(parents=True, exist_ok=True)
    config.template_dir.mkdir(parents=True, exist_ok=True)
    config.assets_dir.mkdir(parents=True, exist_ok=True)
    ensure_sample_templates(config.template_dir, config.assets_dir)
    return config


def reload_settings() -> Settings:
    get_settings.cache_clear()
    global settings
    settings = get_settings()
    return settings


settings = get_settings()

"""Celery application instance."""

from __future__ import annotations

from celery import Celery

from . import config

celery_app = Celery(
    "export_service",
    broker=config.settings.broker_url,
    backend=config.settings.result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_always_eager=config.settings.celery_task_always_eager,
)


__all__ = ["celery_app"]

"""Celery tasks for export processing."""

from __future__ import annotations

import shutil
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from .doc_renderer import DocRenderer
from .excel_renderer import ExcelRenderer
from .models import ExportRequest
from .pdf_converter import LibreOfficeNotFound, docx_to_pdf
from .storage import storage_client
from .worker import celery_app
from .zipper import bundle
from .db import Job, session_scope
from . import config


def _update_job(job_id: str, **kwargs):
    with session_scope() as session:
        job = session.get(Job, job_id)
        if not job:
            return
        for key, value in kwargs.items():
            setattr(job, key, value)


def _finalize(job_id: str, path: Path):
    result = storage_client.save(path, expires_in_hours=config.settings.file_ttl_hours)
    _update_job(
        job_id,
        status="complete",
        result_path=str(result["path"]),
        progress=100,
        expires_at=result["expires_at"],
    )


@celery_app.task(name="export_service.process_export")
def process_export(job_id: str):
    with session_scope() as session:
        job = session.get(Job, job_id)
        if not job:
            return
        payload = ExportRequest(**job.payload)
    _update_job(job_id, status="running", progress=5)
    temp_dir = Path(tempfile.mkdtemp(prefix=f"export_{job_id}_"))
    try:
        doc_renderer = DocRenderer()
        excel_renderer = ExcelRenderer()
        artifacts = []
        docx_path = doc_renderer.render(payload, temp_dir)
        artifacts.append(docx_path)
        _update_job(job_id, progress=40)
        xlsx_path = None
        if payload.options.include_xlsx:
            xlsx_path = excel_renderer.render(payload, temp_dir)
            if xlsx_path:
                artifacts.append(xlsx_path)
        _update_job(job_id, progress=60)
        if payload.options.include_pdf:
            try:
                pdf_path = docx_to_pdf(docx_path, temp_dir)
                artifacts.append(pdf_path)
            except LibreOfficeNotFound as exc:
                _update_job(job_id, status="failed", error_message=str(exc))
                return
        _update_job(job_id, progress=80)
        if payload.options.zip_all:
            zip_path = bundle(job_id, artifacts, temp_dir)
            result_path = zip_path
        else:
            result_path = artifacts[0]
        _finalize(job_id, result_path)
    except Exception as exc:  # noqa: BLE001
        _update_job(job_id, status="failed", error_message=str(exc))
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

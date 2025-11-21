"""FastAPI application exposing export endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from urllib.parse import quote_plus

from .auth import authenticate
from . import config
from .db import Job, session_scope
from .models import ExportJobResponse, ExportRequest, JobStatusResponse
from .jobs import process_export

app = FastAPI(title="Open WebUI Export Service", version="0.1.0")


@app.get("/", response_class=PlainTextResponse)
def root() -> str:
    return "Open WebUI Document Exporter Backend"


@app.post("/api/v1/export", response_model=ExportJobResponse, status_code=202)
def create_export(request: ExportRequest, token: str = Depends(authenticate)):
    job_id = uuid.uuid4().hex
    with session_scope() as session:
        job = Job(
            id=job_id,
            status="pending",
            session_id=request.session_id,
            user_id=request.user_id,
            payload=request.model_dump(),
            options=request.options.model_dump(),
        )
        session.add(job)
    process_export.delay(job_id)
    return ExportJobResponse(job_id=job_id, estimated_time_seconds=15)


@app.get("/api/v1/status/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str, token: str = Depends(authenticate)):
    with session_scope() as session:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        result = None
        if job.status == "complete" and job.result_path:
            result = {
                "download_url": f"/api/v1/download/{job_id}?code={quote_plus(job.download_code or '')}",
                "expires_at": job.expires_at.isoformat() if job.expires_at else None,
            }
        return JobStatusResponse(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            result=result,
            error=job.error_message,
        )


@app.get("/api/v1/download/{job_id}")
def download(job_id: str, code: str | None = None):
    with session_scope() as session:
        job = session.get(Job, job_id)
        if not job or job.status != "complete" or not job.result_path:
            raise HTTPException(status_code=404, detail="Result not available")
        if not code or code != job.download_code:
            raise HTTPException(status_code=401, detail="Invalid or missing download code")
        path = Path(job.result_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="File expired")
        return FileResponse(path, filename=path.name)


@app.delete("/api/v1/jobs/{job_id}")
def delete_job(job_id: str, token: str = Depends(authenticate)):
    with session_scope() as session:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        path = Path(job.result_path) if job.result_path else None
        session.delete(job)
    if path and path.exists():
        path.unlink()
    return {"status": "deleted"}

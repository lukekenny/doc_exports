# Open WebUI Export Service

A FastAPI + Celery service that converts Open WebUI sessions into DOCX, XLSX, optional PDF files, and downloadable ZIP bundles. Includes templates, worker infrastructure, and a sample Open WebUI plugin button.

## Features
- REST API (`/api/v1/export`, `/status/{job_id}`, `/download/{job_id}`)
- DOCX generation via docxtpl + prebuilt templates
- XLSX sheets via pandas/openpyxl with column auto-width, frozen header row
- Optional DOCX→PDF conversion (LibreOffice)
- ZIP bundling with manifest metadata
- Celery background jobs + Redis broker
- Local disk storage with TTL and download endpoint
- Open WebUI client plugin snippet for Export button
- Dockerfile & docker-compose for local dev
- Unit + integration tests (pytest)
- Security & operations docs

## Architecture Overview
```
Client -> FastAPI API -> Redis queue -> Celery worker -> Templates/XLSX -> Storage -> Download URL
```
- **API**: validates payload, enqueues `process_export` Celery job.
- **Worker**: renders DOCX/XLSX/PDF, zips artifacts, stores file, updates DB.
- **DB**: SQLite (dev) storing job status.
- **Storage**: Local folder; swap for S3 by replacing `storage.py` implementation.

See `docs/OPERATIONS.md` and `docs/SECURITY.md` for operational guidance.

## Getting Started

### Requirements
- Python 3.11+
- Redis (for Celery)
- LibreOffice (optional, for PDF conversion)

### Install dependencies
```
pip install -e .[test]
```

### Environment variables
Create `.env` or export vars:
```
API_KEY=dev-secret
DATABASE_URL=sqlite:///./export_jobs.db
REDIS_URL=redis://localhost:6379/0
FILE_TTL_HOURS=24
CELERY_TASK_ALWAYS_EAGER=false
```

### Run locally
1. Start Redis (`docker compose up redis` or local install).
2. Launch API:
   ```
   uvicorn export_service.main:app --reload
   ```
3. Launch worker:
   ```
   celery -A export_service.worker.celery_app worker --loglevel=INFO
   ```
4. POST to `/api/v1/export` with `Authorization: Bearer dev-secret`.

### Docker Compose
`docker-compose.yml` runs API, worker, redis, and minio (optional) for development.
```
docker compose up --build
```
API will listen on `http://localhost:8000`.

For prebuilt images hosted on GitHub Container Registry (e.g., when deploying through Portainer), use `docker-compose.portainer.yml`. It expects two environment variables that point at the published images:

```
API_IMAGE=ghcr.io/<org>/doc_exports:latest
WORKER_IMAGE=ghcr.io/<org>/doc_exports-worker:latest
docker compose -f docker-compose.portainer.yml up -d
```

Volumes defined in that file keep `/data`, `/app/storage`, and `/app/templates` persistent across container restarts so Portainer can manage upgrades safely.

## Templates
Sample `.docx` templates are generated on demand the first time the app imports its settings. No binary documents are stored in git—`export_service.template_setup` writes simple Word files that already contain the docxtpl placeholders referenced in `docs/TEMPLATES.md` and drops a placeholder logo under `templates/assets/logo.png`.

To recreate or customize them locally run:

```
python -m export_service.template_setup --force
```

You can then open the generated `.docx` files in Word, make stylistic tweaks, and keep them outside of version control.

## Testing
```
pytest
```
Sets `CELERY_TASK_ALWAYS_EAGER=1` so Celery tasks run synchronously.

## Open WebUI Integration
`openwebui_plugin/export_tool.py` is a fully compliant Open WebUI **Tools** plugin. Paste the contents into the Tools workspace ("Create Tool" → "Import from file") to expose a callable `export_session` function to the assistant or code interpreter. Configure the following environment variables in Open WebUI so the tool can reach this service:

| Variable | Purpose |
| --- | --- |
| `EXPORT_SERVICE_URL` | Base URL for the FastAPI export service (e.g., `http://localhost:8000`). |
| `EXPORT_API_KEY` | Bearer token that must match the `API_KEY` configured on the export service. |
| `EXPORT_POLL_INTERVAL` | Optional override (seconds) for status polling cadence. |
| `EXPORT_POLL_TIMEOUT` | Optional override (seconds) for how long to wait before returning an in-progress status. |

The tool accepts session metadata (title, summary, sections, tables, and rendering options), queues an export job, and optionally waits for the download URL to become available—all from within the native Python tool runtime described in the [Open WebUI plugin documentation](https://openwebui.com/).

## Background Jobs
- Celery task `export_service.process_export`
- Redis broker/back-end by default
- Worker cleans temp files and updates job progress
- Configure concurrency via `CELERY_WORKER_CONCURRENCY` when starting Celery

## Storage & Cleanup
- Generated files saved under `storage/` with TTL (`FILE_TTL_HOURS`).
- `docs/OPERATIONS.md` covers retention + cron cleanup.

## Deployment Notes
- Build API container (FastAPI + Gunicorn/Uvicorn) using provided Dockerfile.
- Worker container shares codebase but runs `celery` entrypoint.
- Use S3-compatible storage in production for multi-node downloads.
- Integrate with monitoring (Prometheus) via Celery exporters.

## Acceptance Tests
See `docs/ACCEPTANCE.md` for manual verification checklist.

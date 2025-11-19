# Operational Runbook

## Components
- **API**: FastAPI app served by Uvicorn/Gunicorn. Stateless, can scale horizontally.
- **Worker**: Celery worker consuming from Redis. Handles conversions and uploads.
- **Redis**: Message broker and backend.
- **Database**: SQLite (dev) / Postgres (prod) storing job metadata.
- **Storage**: Local `storage/` folder (dev) / S3 bucket (prod).

## Day-2 Operations
1. **Deployments**
   - Build Docker images via CI and push to registry.
   - Use `docker-compose` locally or Helm/Kubernetes in production.
   - Rolling deploy API first, then workers.
2. **Scaling**
   - Increase worker replicas when queue latency grows; monitor Celery queue length.
   - Limit LibreOffice concurrency via Celery worker pool size or task routing.
3. **Monitoring**
   - Expose Prometheus metrics (Celery + custom). Alert on queue backlog, job failures, disk usage.
   - Centralize logs (JSON) with job_id, user_id, template.
4. **Cleanup**
   - Schedule cron to purge `storage/` files older than TTL and delete DB rows.
   - Use `/api/v1/jobs/{id}` DELETE for manual cleanup.

## Troubleshooting
- **LibreOffice stuck**: kill PID, restart worker container, requeue job.
- **Disk full**: run cleanup script, increase volume, or switch to S3.
- **Redis outage**: API should return 503 to throttle new jobs. Workers auto-reconnect when broker returns.
- **Slow exports**: inspect template loops, reduce data size, add caching for session JSON.

## Configuration Reference
Key environment variables:
- `API_KEY`: required token for clients.
- `DATABASE_URL`: `postgresql+psycopg://user:pass@host/db` in production.
- `REDIS_URL`: Celery broker/backend.
- `FILE_TTL_HOURS`: retention window for stored artifacts.
- `ALLOWED_TEMPLATES`: comma-separated list to enable tenant-specific templates.
- `CELERY_TASK_ALWAYS_EAGER`: set to `true` for tests.

## Fonts & Localization
- Place fonts under `/usr/share/fonts` in the worker image.
- Set `locale` option in payload to inform downstream formatting logic.

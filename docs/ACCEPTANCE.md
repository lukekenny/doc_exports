# Acceptance Checklist

## Functional
- [ ] POST `/api/v1/export` accepts valid payload, returns `202` with job id.
- [ ] Job transitions pending -> running -> complete with result link.
- [ ] Generated DOCX follows template placeholders (title, summary, sections, tables, logo).
- [ ] XLSX output contains a sheet per table with frozen header row and adjusted columns.
- [ ] ZIP bundle includes manifest JSON.
- [ ] Download endpoint streams stored artifact.

## Security
- [ ] Requests without API key return 401.
- [ ] Job deletion restricted to authenticated callers.
- [ ] Templates restricted to whitelisted files.

## Operations
- [ ] Temp directories deleted after job.
- [ ] Storage TTL enforced via scheduler (manual test by changing `FILE_TTL_HOURS`).
- [ ] Worker retries (configure Celery `--max-tasks-per-child` or retries) verified.

## Tests
- [ ] `pytest` succeeds locally.
- [ ] Integration test covers POST/status/download happy path.

## Documentation
- [ ] README updated with setup, env vars, architecture.
- [ ] Template editing instructions available.
- [ ] Open WebUI plugin snippet present.

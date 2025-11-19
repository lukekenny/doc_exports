# Security & Data Protection

## Authentication
- The API enforces bearer or API key authentication for every endpoint. Configure the `API_KEY` environment variable (or integrate with your IdP) and distribute tokens securely.
- Jobs store the `session_id` and optional `user_id` of the caller for auditing. Use a reverse proxy or JWT middleware to ensure the caller is authorized to access that session.

## Input Validation & Limits
- The `ExportRequest` schema validates section/table counts and restricts table rows to 100k.
- Incoming strings are bounded to prevent template or memory abuse.
- Only pre-registered templates located in `templates/` can be used. Arbitrary template uploads are blocked to avoid template-injection attacks.

## Storage & Retention
- Artifacts are persisted in `storage/` with TTL (default 24h). Configure `FILE_TTL_HOURS` or move to S3 to apply lifecycle policies.
- Temporary directories are deleted after each job. Use OS-level tmpfs or container filesystem with automatic cleanup in production.

## Conversion Sandbox
- LibreOffice conversions run in a separate process invoked via CLI. Limit concurrent conversions by tuning worker concurrency and consider cgroup/namespace isolation.
- For untrusted HTML/Markdown, sanitize before injecting into templates.

## Virus Scanning & Compliance
- Hook in ClamAV or platform scanning before making download links available when handling untrusted input.
- Log audit trails: who triggered exports, payload metadata, resource usage, and download events.

## Transport Security
- Terminate TLS at the ingress/load balancer. Presigned URLs should be HTTPS and expire alongside stored files.

## Fonts & Assets
- Bundle the fonts required by your templates in the worker container to avoid rendering discrepancies.
- Only allow administrators to modify template assets and logos.

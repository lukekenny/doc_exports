"""
name: Document Exporter
version: 0.3.0
min_sdk_version: 0.0.1
description: |
  Native Python tool for Open WebUI that queues document export jobs via the
  FastAPI service included in this repository. The tool submits the current
  session metadata, polls job status, and returns download links when
  available.

  **Supported document types**
  - Word document (`doc` / `docx`)
  - Excel spreadsheet (`xlsx`)
  - PowerPoint presentation (`pptx`)
  - PDF
  - Plain text (`txt`)
  - ZIP bundle (automatically used when multiple formats are requested)

  Short identifier: `doc_exports`.

  Ask the assistant to be explicit about the desired format. Example prompts:
  - "Export a Word report using the summary template."
  - "Generate an Excel spreadsheet of the tables only."
  - "Build a PowerPoint presentation from these sections."
  - "Produce a PDF and text summary, zipped together."

  **XLSX-only behavior**

  To request only an Excel workbook (no DOCX/PDF/TXT), set `requested_formats`
  to include `xlsx` (or say "excel"/"spreadsheet") and the tool will:
  - Enable `include_xlsx`
  - Disable `include_pdf`, `include_pptx`, and `include_txt`
  - Set `zip_all` to false unless multiple formats are requested
  - Set `primary_format` to "xlsx"

  The `template` field is required for DOCX/PDF but is ignored for XLSX-only
  exports.

requirements: httpx
"""

from __future__ import annotations

import asyncio
import os
from urllib.parse import urljoin
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field


class SectionInput(BaseModel):
    """Simple heading/body pair that becomes a DOCX section."""

    heading: str = Field(..., description="Section heading rendered as a title")
    body: str = Field(
        "",
        description="Rich text or markdown content that should appear inside the section",
    )


class TableInput(BaseModel):
    """Tabular payload rendered as XLSX/Word tables."""

    name: str = Field(..., description="Human friendly table title")
    columns: List[str] = Field(
        ...,
        description="Ordered column names; rows should only use these keys",
    )
    rows: List[Union[Dict[str, Any], List[Any]]] = Field(
        ...,
        description=(
            "List of rows matching the declared columns. Each row may be a dict "
            "mapping column->value OR a list whose values correspond to columns "
            "by position (extra values kept as column_# keys; missing values "
            "padded with null)."
        ),
    )


class ExportOptionsInput(BaseModel):
    template: str = Field(
        "summary_template.docx",
        description=(
            "Base DOCX template used when rendering Word/PDF output. "
            "Ignored for XLSX-only, PPTX-only, or TXT-only exports."
        ),
    )
    include_pdf: bool = Field(False, description="Toggle DOCX to PDF conversion")
    include_pptx: bool = Field(False, description="Render a PowerPoint deck (pptx)")
    include_xlsx: bool = Field(
        False, description="Render spreadsheet output (xlsx). Enable when the user asks for spreadsheets."
    )
    include_txt: bool = Field(False, description="Render a plain text summary (txt)")
    zip_all: bool = Field(
        True,
        description="Bundle every artifact in a .zip file; automatically enabled when multiple formats are requested",
    )
    locale: str = Field("en-US", description="Locale passed to docxtpl/pandas formatters")
    page_orientation: str = Field(
        "portrait",
        description="DOCX orientation, e.g. portrait or landscape",
    )
    primary_format: str = Field(
        "docx",
        description=(
            "Primary file format to return when ZIP bundling is disabled (docx, xlsx, pptx, pdf, or txt)."
        ),
    )


class Tools:
    """Collection of callable functions exposed to Open WebUI."""

    def __init__(self) -> None:
        self.default_base_url = os.getenv(
            "EXPORT_SERVICE_URL", "http://oracle-docker.smallcreek.com.au:8123"
        )
        self.default_api_key = os.getenv("EXPORT_API_KEY", "change-me")
        self.default_poll_interval = float(os.getenv("EXPORT_POLL_INTERVAL", "1.5"))
        self.default_poll_timeout = float(os.getenv("EXPORT_POLL_TIMEOUT", "60"))
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    async def export_session(
        self,
        session_id: str,
        title: str,
        summary: str,
        user_id: Optional[str] = None,
        sections: Optional[List[SectionInput]] = None,
        tables: Optional[List[TableInput]] = None,
        options: Optional[ExportOptionsInput] = None,
        requested_formats: Optional[List[str]] = None,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        wait_for_completion: bool = True,
        poll_interval_seconds: Optional[float] = None,
        poll_timeout_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Submit the current Open WebUI session to the export microservice.

        Args:
            session_id: Open WebUI session identifier.
            title: Title of the export bundle.
            summary: Short human readable description.
            user_id: Optional user identifier that is stored next to the job.
            sections: List of section payloads that become DOCX paragraphs.
            tables: List of tabular datasets rendered inside XLSX/DOCX.
            options: Extra rendering toggles (template file, PDF/XLSX switches).
            requested_formats: List of human-friendly format names (docx, word, pdf, xlsx, spreadsheet,
                pptx, presentation, txt, text, zip). These inputs are normalized into the correct rendering flags
                so the export service receives the right document request.
            api_base: Override for the export service URL (defaults to EXPORT_SERVICE_URL).
            api_key: Override for the bearer token (defaults to EXPORT_API_KEY).
            wait_for_completion: When False the method returns immediately after queueing the job.
            poll_interval_seconds: How often to poll `/status`; defaults to EXPORT_POLL_INTERVAL.
            poll_timeout_seconds: Max seconds to wait before returning with the latest job status.

        Returns:
            A dictionary with the job identifier, the latest status, and download metadata when ready.
        """

        resolved_token = api_key or self.default_api_key
        if not resolved_token:
            raise RuntimeError(
                "Missing API key. Set EXPORT_API_KEY or pass api_key explicitly when calling the tool."
            )

        base_url = api_base or self.default_base_url
        if not base_url:
            raise RuntimeError("Missing export service URL. Set EXPORT_SERVICE_URL or pass api_base explicitly.")

        payload = {
            "session_id": session_id,
            "title": title,
            "summary": summary,
            "user_id": user_id,
            "sections": [
                section.model_dump() if isinstance(section, SectionInput) else section
                for section in (sections or [])
            ],
            "tables": [
                table.model_dump() if isinstance(table, TableInput) else table for table in (tables or [])
            ],
            "options": self._coerce_options(options, requested_formats=requested_formats),
        }

        headers = {"Authorization": f"Bearer {resolved_token}"}

        try:
            async with httpx.AsyncClient(base_url=base_url, timeout=self.timeout) as client:
                response = await client.post("/api/v1/export", json=payload, headers=headers)
                response.raise_for_status()
                job_data = response.json()
                job_id = job_data["job_id"]

                if not wait_for_completion:
                    return {
                        "job_id": job_id,
                        "status": "queued",
                        "estimated_time_seconds": job_data.get("estimated_time_seconds", 10),
                    }

                poll_interval = poll_interval_seconds or self.default_poll_interval
                poll_timeout = poll_timeout_seconds or self.default_poll_timeout
                loop = asyncio.get_running_loop()
                deadline = loop.time() + poll_timeout

                while True:
                    status_response = await client.get(f"/api/v1/status/{job_id}", headers=headers)
                    status_response.raise_for_status()
                    status_payload = status_response.json()
                    current_status = status_payload.get("status", "unknown")

                    if current_status == "complete" and status_payload.get("result"):
                        result = status_payload["result"]
                        download_url = urljoin(f"{base_url.rstrip('/')}/", result["download_url"])
                        return {
                            "job_id": job_id,
                            "status": "complete",
                            "download_url": download_url,
                            "expires_at": result.get("expires_at"),
                        }

                    if current_status == "failed":
                        raise RuntimeError(status_payload.get("error") or "Export job failed")

                    if loop.time() >= deadline:
                        return {
                            "job_id": job_id,
                            "status": current_status,
                            "progress": status_payload.get("progress", 0),
                        }

                    await asyncio.sleep(poll_interval)
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Export service returned {exc.response.status_code}: {exc.response.text.strip()}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Unable to reach export service at {base_url}: {exc}") from exc

    @staticmethod
    def _coerce_options(
        value: Optional[ExportOptionsInput | Dict[str, Any]],
        *,
        requested_formats: Optional[List[str]],
    ) -> Dict[str, Any]:
        if isinstance(value, ExportOptionsInput):
            base_options = value.model_dump()
        elif isinstance(value, dict):
            base_options = ExportOptionsInput(**value).model_dump()
        else:
            base_options = ExportOptionsInput().model_dump()
        if requested_formats:
            normalized = {fmt.strip().lower() for fmt in requested_formats if fmt}
            format_flags = {
                "doc": "docx",
                "docx": "docx",
                "word": "docx",
                "word document": "docx",
                "xlsx": "xlsx",
                "excel": "xlsx",
                "spreadsheet": "xlsx",
                "sheet": "xlsx",
                "ppt": "pptx",
                "pptx": "pptx",
                "powerpoint": "pptx",
                "presentation": "pptx",
                "pdf": "pdf",
                "txt": "txt",
                "text": "txt",
                "plain text": "txt",
                "zip": "zip",
                "zip file": "zip",
                "archive": "zip",
            }
            resolved_targets = {format_flags.get(fmt, fmt) for fmt in normalized}
            base_options["include_pdf"] = "pdf" in resolved_targets
            base_options["include_xlsx"] = "xlsx" in resolved_targets
            base_options["include_pptx"] = "pptx" in resolved_targets
            base_options["include_txt"] = "txt" in resolved_targets
            if len(resolved_targets) > 1:
                base_options["zip_all"] = True
            if "zip" in resolved_targets:
                base_options["zip_all"] = True
            primary_preference = next(
                (fmt for fmt in ("docx", "xlsx", "pptx", "pdf", "txt") if fmt in resolved_targets),
                base_options.get("primary_format", "docx"),
            )
            base_options["primary_format"] = primary_preference
        return base_options

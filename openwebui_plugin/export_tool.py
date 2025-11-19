"""
name: session_exporter
version: 0.2.0
min_sdk_version: 0.0.1
description: |
  Native Python tool for Open WebUI that queues document export jobs via the
  FastAPI service included in this repository. The tool submits the current
  session metadata, polls job status, and returns download links when
  available.
requirements: httpx
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

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
        default_factory=list,
        description="Ordered column names; rows should only use these keys",
    )
    rows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of rows matching the declared columns",
    )


class ExportOptionsInput(BaseModel):
    template: str = Field(
        "summary_template.docx",
        description="Name of the DOCX template available inside the export service",
    )
    include_pdf: bool = Field(False, description="Toggle DOCX to PDF conversion")
    include_pptx: bool = Field(False, description="Render a PowerPoint deck")
    include_xlsx: bool = Field(True, description="Render spreadsheet output")
    zip_all: bool = Field(True, description="Bundle every artifact in a .zip file")
    locale: str = Field("en-US", description="Locale passed to docxtpl/pandas formatters")
    page_orientation: str = Field(
        "portrait",
        description="DOCX orientation, e.g. portrait or landscape",
    )


class Tools:
    """Collection of callable functions exposed to Open WebUI."""

    def __init__(self) -> None:
        self.default_base_url = os.getenv("EXPORT_SERVICE_URL", "http://localhost:8000")
        self.default_api_key = os.getenv("EXPORT_API_KEY")
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
            "options": self._coerce_options(options),
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
                        download_url = httpx.URL(base_url).join(result["download_url"]).human_repr()
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
    def _coerce_options(value: Optional[ExportOptionsInput | Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(value, ExportOptionsInput):
            return value.model_dump()
        if isinstance(value, dict):
            return ExportOptionsInput(**value).model_dump()
        return ExportOptionsInput().model_dump()

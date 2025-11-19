"""Pydantic models for requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, RootModel, field_validator


class Section(BaseModel):
    heading: str = Field(..., min_length=1, max_length=256)
    body: str = Field("", max_length=5000)


class TableRow(RootModel[dict]):
    def dict(self, *args, **kwargs):  # type: ignore[override]
        return self.root

    def model_dump(self, *args, **kwargs):  # type: ignore[override]
        return self.root


class Table(BaseModel):
    name: str = Field(..., min_length=1)
    columns: List[str]
    rows: List[TableRow]

    @field_validator("rows")
    def limit_rows(cls, value):
        if len(value) > 100000:
            raise ValueError("table row limit exceeded")
        return value


class ExportOptions(BaseModel):
    template: str = Field("summary_template.docx")
    include_pdf: bool = False
    include_pptx: bool = False
    include_xlsx: bool = True
    zip_all: bool = True
    locale: str = Field("en-US")
    page_orientation: str = Field("portrait")


class ExportRequest(BaseModel):
    title: str
    summary: str
    session_id: str
    user_id: Optional[str] = None
    sections: List[Section] = Field(default_factory=list)
    tables: List[Table] = Field(default_factory=list)
    options: ExportOptions = Field(default_factory=ExportOptions)

    @field_validator("sections", "tables", mode="before")
    def default_empty(cls, value):
        return value or []


class ExportJobResponse(BaseModel):
    job_id: str
    estimated_time_seconds: int = 10


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    result: Optional[dict] = None
    error: Optional[str] = None


class DownloadResponse(BaseModel):
    filename: str
    expires_at: Optional[datetime]

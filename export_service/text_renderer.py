"""Plain text rendering for export payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import ExportRequest


class TextRenderer:
    """Render a human-readable text summary of an export request."""

    def render(self, request: ExportRequest, output_dir: Path) -> Path:
        output_path = output_dir / "report.txt"
        lines = self._build_lines(request)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def _build_lines(self, request: ExportRequest) -> list[str]:
        lines: list[str] = []
        title = request.title.strip() if request.title else "Export"
        underline = "=" * len(title)
        lines.extend([title, underline, ""])  # Title block

        if request.summary:
            lines.extend(["Summary:", request.summary.strip(), ""])  # Summary block

        if request.sections:
            lines.append("Sections:")
            for section in request.sections:
                heading = section.heading.strip()
                lines.extend([
                    f"- {heading}",
                    section.body.strip(),
                    "",
                ])

        if request.tables:
            lines.append("Tables:")
            for table in request.tables:
                lines.append(f"- {table.name}")
                if table.columns:
                    lines.append("  | " + " | ".join(table.columns) + " |")
                for row in table.rows:
                    data = row.root if hasattr(row, "root") else row
                    if isinstance(data, dict) and "__root__" in data and isinstance(data["__root__"], dict):
                        data = data["__root__"]
                    row_dict = data if isinstance(data, dict) else {}
                    values = [row_dict.get(col, "") for col in table.columns]
                    lines.append("  | " + " | ".join(self._stringify(values)) + " |")
                lines.append("")

        return lines or ["Export"]

    @staticmethod
    def _stringify(values: Iterable[object]) -> list[str]:
        return ["" if value is None else str(value) for value in values]

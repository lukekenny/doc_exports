"""Excel rendering using pandas and openpyxl."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font

from .models import ExportRequest


class ExcelRenderer:
    def render(self, request: ExportRequest, output_dir: Path) -> Path | None:
        if not request.tables:
            return None
        output_path = output_dir / "tables.xlsx"
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for table in request.tables:
                df = pd.DataFrame([row.dict() for row in table.rows])
                if df.empty:
                    df = pd.DataFrame(columns=table.columns)
                if table.columns:
                    available = [col for col in table.columns if col in df.columns]
                    if available:
                        df = df[available]
                sheet_name = table.name[:31] or "Sheet1"
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                sheet = writer.sheets[sheet_name]
                for column_cells in sheet.columns:
                    max_length = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
                    adjusted_width = min(max(12, max_length + 2), 60)
                    sheet.column_dimensions[column_cells[0].column_letter].width = adjusted_width
                for cell in sheet[1]:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal="center")
                sheet.freeze_panes = "A2"
        return output_path

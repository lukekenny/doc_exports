"""DOCX rendering using docxtpl templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from docxtpl import DocxTemplate, InlineImage
from docx.shared import Cm

from . import config
from .models import ExportRequest


class DocRenderer:
    def __init__(self, template_dir: Path | None = None):
        self.template_dir = template_dir or config.settings.template_dir

    def render(self, request: ExportRequest, output_dir: Path) -> Path:
        template_name = request.options.template
        if template_name not in config.settings.allowed_templates:
            raise ValueError(f"Template {template_name} is not allowed")
        template_path = self.template_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found")
        tpl = DocxTemplate(template_path)
        context = self._build_context(request, tpl)
        output_path = output_dir / "report.docx"
        tpl.render(context)
        tpl.save(output_path)
        return output_path

    def _build_context(self, request: ExportRequest, tpl: DocxTemplate) -> Dict[str, Any]:
        context = request.model_dump()
        context["tables_json"] = json.dumps([table.model_dump() for table in request.tables])
        logo_path = config.settings.assets_dir / "logo.png"
        if logo_path.exists():
            context["logo"] = InlineImage(tpl, str(logo_path), width=Cm(3))
        else:
            context["logo"] = None
        return context

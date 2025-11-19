"""Utilities that ensure sample docxtpl templates exist without storing binaries in git."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from PIL import Image, ImageDraw, ImageFont


def ensure_sample_templates(template_dir: Path, assets_dir: Path, force: bool = False) -> None:
    """Create simple DOCX templates + logo if they are missing."""

    template_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    _create_logo(assets_dir / "logo.png", force=force)
    _create_summary_template(template_dir / "summary_template.docx", force=force)
    _create_full_report_template(template_dir / "full_report_template.docx", force=force)


def _create_logo(path: Path, force: bool = False) -> None:
    if path.exists() and not force:
        return

    image = Image.new("RGB", (640, 200), color="#0d47a1")
    draw = ImageDraw.Draw(image)
    text = "Open WebUI"
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
    except OSError:
        font = ImageFont.load_default()
    bbox = font.getbbox(text)
    text_width = draw.textlength(text, font=font)
    text_height = bbox[3] - bbox[1]
    draw.text(((640 - text_width) / 2, (200 - text_height) / 2), text, font=font, fill="white")
    image.save(path)


def _create_summary_template(path: Path, force: bool = False) -> None:
    if path.exists() and not force:
        return

    doc = Document()
    doc.core_properties.title = "Summary Report"

    logo_para = doc.add_paragraph("{{ logo }}")
    logo_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.add_heading("{{ title }}", level=1)
    doc.add_paragraph("{{ summary }}")

    doc.add_paragraph("{% if sections %}")
    doc.add_paragraph("{% for section in sections %}")
    doc.add_heading("{{ section.heading }}", level=2)
    doc.add_paragraph("{{ section.body }}")
    doc.add_paragraph("{% endfor %}")
    doc.add_paragraph("{% endif %}")

    doc.add_heading("Tables", level=2)
    doc.add_paragraph("{% if tables %}")
    doc.add_paragraph("{{ tables_json }}")
    doc.add_paragraph("{% else %}No tables supplied.{% endif %}")

    doc.save(path)


def _create_full_report_template(path: Path, force: bool = False) -> None:
    if path.exists() and not force:
        return

    doc = Document()
    doc.core_properties.title = "Full Report"
    doc.add_paragraph("{{ logo }}").alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("{{ title }}", level=1)
    summary_para = doc.add_paragraph("{{ summary }}")
    if summary_para.runs:
        summary_para.runs[0].font.size = Pt(12)

    doc.add_paragraph("{% for section in sections %}")
    doc.add_heading("{{ section.heading }}", level=2)
    doc.add_paragraph("{{ section.body }}")
    doc.add_paragraph("{% endfor %}")

    doc.add_heading("Tables", level=2)
    doc.add_paragraph("{% for table in tables %}")
    doc.add_heading("{{ table.name }}", level=3)
    doc.add_paragraph("Columns: {{ table.columns }}")
    doc.add_paragraph("{% for row in table.rows %}Row: {{ row.__root__ }}{% endfor %}")
    doc.add_paragraph("{% endfor %}")

    footer = doc.sections[0].footer
    if not footer.paragraphs:
        footer.add_paragraph()
    footer.paragraphs[0].text = "Session {{ session_id }} — Generated {{ title }}"

    doc.save(path)


def main() -> None:  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description="Generate sample DOCX templates and assets.")
    parser.add_argument("--template-dir", type=Path, default=Path("templates"))
    parser.add_argument("--assets-dir", type=Path, default=Path("templates/assets"))
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    ensure_sample_templates(args.template_dir, args.assets_dir, force=args.force)
    print(f"Templates ready under {args.template_dir}")


if __name__ == "__main__":  # pragma: no cover
    main()

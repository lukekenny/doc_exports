"""DOCX to PDF conversion helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class LibreOfficeNotFound(RuntimeError):
    pass


def docx_to_pdf(docx_path: Path, output_dir: Path) -> Path:
    executable = shutil.which("libreoffice")
    if not executable:
        raise LibreOfficeNotFound("LibreOffice is not installed in this environment")
    subprocess.run(
        [
            executable,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(docx_path),
        ],
        check=True,
        capture_output=True,
    )
    pdf_path = output_dir / (docx_path.stem + ".pdf")
    if not pdf_path.exists():
        raise FileNotFoundError("PDF conversion failed")
    return pdf_path

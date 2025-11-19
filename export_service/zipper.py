"""ZIP bundling utilities."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def bundle(job_id: str, files: list[Path], output_dir: Path) -> Path:
    manifest = []
    for file_path in files:
        manifest.append(
            {
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }
        )
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps({"job_id": job_id, "files": manifest}, indent=2))
    zip_path = output_dir / f"{job_id}_export.zip"
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zip_file:
        for file_path in files:
            zip_file.write(file_path, arcname=file_path.name)
        zip_file.write(manifest_path, arcname="manifest.json")
    return zip_path

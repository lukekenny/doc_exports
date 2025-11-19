"""Storage helpers for generated files."""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from . import config


class LocalStorage:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or config.settings.storage_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, source: Path, expires_in_hours: int | None = None) -> dict:
        file_id = uuid.uuid4().hex
        destination = self.base_dir / f"{file_id}_{source.name}"
        shutil.copy2(source, destination)
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        return {"file_id": file_id, "path": destination, "expires_at": expires_at}

    def resolve(self, file_id: str) -> Path | None:
        matches = list(self.base_dir.glob(f"{file_id}_*"))
        return matches[0] if matches else None


storage_client = LocalStorage()

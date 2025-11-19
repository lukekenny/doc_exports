import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

DB_PATH = Path("/tmp/export_service_test.db")
if DB_PATH.exists():
    DB_PATH.unlink()

os.environ["API_KEY"] = "test-key"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "1"
os.environ["DATABASE_URL"] = f"sqlite:////{DB_PATH}"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from export_service.config import reload_settings, settings  # noqa: E402
from export_service.db import reload_engine  # noqa: E402

reload_settings()
reload_engine()
from export_service.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def cleanup_db():
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", tmp_path / "storage")
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    with TestClient(app) as test_client:
        yield test_client

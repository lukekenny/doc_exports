import sqlite3

from sqlalchemy import inspect

import export_service.config as config
import export_service.db as db


def test_migration_adds_download_code(monkeypatch, tmp_path):
    legacy_db = tmp_path / "legacy.db"
    connection = sqlite3.connect(legacy_db)
    connection.execute(
        """
        CREATE TABLE jobs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at DATETIME,
            updated_at DATETIME,
            session_id TEXT NOT NULL,
            user_id TEXT,
            payload JSON,
            options JSON,
            progress INTEGER,
            result_path TEXT,
            expires_at DATETIME,
            error_message TEXT
        )
        """
    )
    connection.commit()
    connection.close()

    original_url = config.settings.database_url
    monkeypatch.setattr(config.settings, "database_url", f"sqlite:////{legacy_db}")

    db.reload_engine()

    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("jobs")}
    assert "download_code" in columns

    monkeypatch.setattr(config.settings, "database_url", original_url)
    db.reload_engine()

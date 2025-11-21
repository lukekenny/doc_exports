"""Database utilities and models."""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, MetaData, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from . import config

metadata = MetaData()
Base = declarative_base(metadata=metadata)


def _connect_args(url: str):
    return {"check_same_thread": False} if url.startswith("sqlite") else {}


def create_db_engine():
    return create_engine(config.settings.database_url, connect_args=_connect_args(config.settings.database_url))


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    options = Column(JSON, nullable=False, default=dict)
    progress = Column(Integer, nullable=False, default=0)
    result_path = Column(String, nullable=True)
    download_code = Column(String, nullable=True, unique=True)
    expires_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "job_id": self.id,
            "status": self.status,
            "progress": self.progress,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "options": self.options or {},
            "result_path": self.result_path,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "error": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


Base.metadata.create_all(engine)


def reload_engine():
    global engine, SessionLocal
    engine.dispose()
    engine = create_db_engine()
    SessionLocal.configure(bind=engine)
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Generator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

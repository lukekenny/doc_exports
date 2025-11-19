"""Simple API key authentication helpers."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from . import config

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def authenticate(api_key: str | None = Security(api_key_header), credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme)) -> str:
    token = api_key or (credentials.credentials if credentials else None)
    if not token or token != config.settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return token

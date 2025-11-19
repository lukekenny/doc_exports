"""Simple API key authentication helpers."""

from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, APIKeyQuery, HTTPAuthorizationCredentials, HTTPBearer

from . import config

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def authenticate(
    api_key_header_value: str | None = Security(api_key_header),
    api_key_query_value: str | None = Security(api_key_query),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> str:
    token = api_key_header_value or api_key_query_value or (credentials.credentials if credentials else None)
    if not token or token != config.settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return token

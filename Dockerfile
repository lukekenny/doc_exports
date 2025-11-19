FROM python:3.11-slim

WORKDIR /app
# Copy the dependency metadata and package source first so pip install can
# succeed (and leverage Docker layer caching).
COPY pyproject.toml /app/
COPY export_service /app/export_service
RUN pip install --no-cache-dir -e .

# Copy the rest of the source tree after dependencies are installed.
COPY . /app
ENV API_KEY=dev-secret \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000

CMD ["uvicorn", "export_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

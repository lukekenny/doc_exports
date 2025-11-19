FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .
COPY . /app
ENV API_KEY=dev-secret \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000

CMD ["uvicorn", "export_service.main:app", "--host", "0.0.0.0", "--port", "8000"]

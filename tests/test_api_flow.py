import os

from export_service.models import ExportRequest, ExportOptions, Section, Table, TableRow


def payload():
    return {
        "title": "Monthly Sales",
        "summary": "Summary",
        "session_id": "session-1",
        "user_id": "user-1",
        "sections": [{"heading": "Overview", "body": "Body"}],
        "tables": [
            {
                "name": "Sales",
                "columns": ["region", "sales"],
                "rows": [{"region": "East", "sales": 100}],
            }
        ],
        "options": {"include_pdf": False, "include_txt": True, "zip_all": True},
    }


def test_export_flow(client):
    response = client.post("/api/v1/export", json=payload(), headers={"Authorization": "Bearer test-key"})
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    status = client.get(f"/api/v1/status/{job_id}", headers={"Authorization": "Bearer test-key"})
    assert status.status_code == 200
    data = status.json()
    assert data["status"] in {"complete", "running", "pending", "failed"}
    if data["status"] == "complete":
        download = client.get(data["result"]["download_url"], headers={"Authorization": "Bearer test-key"})
        assert download.status_code == 200

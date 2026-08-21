import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_automation_api_lifecycle():
    # 1. Trigger Automation Run
    res_start = client.post("/api/automation/run", json={"job_id": 101})
    assert res_start.status_code == 200
    run_data = res_start.json()
    assert "state" in run_data
    run_id = run_data["id"]

    # 2. List Runs
    res_list = client.get("/api/automation/runs")
    assert res_list.status_code == 200
    assert len(res_list.json()) > 0

    # 3. Get Run Detail
    res_detail = client.get(f"/api/automation/runs/{run_id}")
    assert res_detail.status_code == 200

    # 4. Get Action Logs
    res_logs = client.get(f"/api/automation/runs/{run_id}/actions")
    assert res_logs.status_code == 200

    # 5. Get Screenshots Metadata
    res_shots = client.get(f"/api/automation/runs/{run_id}/screenshots")
    assert res_shots.status_code == 200
    assert "screenshots" in res_shots.json()

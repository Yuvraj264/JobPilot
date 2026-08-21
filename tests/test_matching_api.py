import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_matching_api_endpoints():
    """Test matching REST API endpoints."""
    # 1. Trigger Batch Matching
    res_run = client.post("/api/matching/run", json={"limit": 50})
    assert res_run.status_code == 200
    assert "jobs_evaluated" in res_run.json()

    # 2. Get Matching Stats
    res_stats = client.get("/api/matching/stats")
    assert res_stats.status_code == 200
    assert res_stats.json()["jobs_evaluated"] > 0

    # 3. List Job Matches
    res_list = client.get("/api/matching/jobs")
    assert res_list.status_code == 200
    matches = res_list.json()
    assert len(matches) > 0

    job_id = matches[0]["job_id"]

    # 4. Get Match Details for single job
    res_detail = client.get(f"/api/matching/job/{job_id}")
    assert res_detail.status_code == 200
    assert "explanation" in res_detail.json()

    # 5. Get Config
    res_config = client.get("/api/matching/config")
    assert res_config.status_code == 200
    assert "weight_skills" in res_config.json()

    # 6. Update Config
    res_put = client.put("/api/matching/config", json={"threshold_apply": 88.0})
    assert res_put.status_code == 200
    assert res_put.json()["threshold_apply"] == 88.0

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_job_api_lifecycle():
    """Test job sources listing, mock discovery execution, job search, stats, and status update."""
    # 1. List Job Sources
    res_sources = client.get("/api/jobs/sources")
    assert res_sources.status_code == 200
    assert len(res_sources.json()) >= 1

    # 2. Trigger Mock Discovery
    res_disc = client.post("/api/jobs/discover/mock")
    assert res_disc.status_code == 200
    disc_summary = res_disc.json()
    assert disc_summary["jobs_discovered"] >= 15

    # 3. List Jobs
    res_jobs = client.get("/api/jobs")
    assert res_jobs.status_code == 200
    jobs = res_jobs.json()
    assert len(jobs) > 0
    job_id = jobs[0]["id"]

    # 4. Search Jobs
    res_search = client.get("/api/jobs/search?q=QA")
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1

    # 5. Get Job Detail
    res_detail = client.get(f"/api/jobs/{job_id}")
    assert res_detail.status_code == 200
    assert "description" in res_detail.json()

    # 6. Update Job Status
    res_patch = client.patch(f"/api/jobs/{job_id}/status", json={"status": "EXPIRED"})
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "EXPIRED"

    # 7. Get Job Stats
    res_stats = client.get("/api/jobs/stats")
    assert res_stats.status_code == 200
    assert res_stats.json()["total_jobs"] > 0

    # 8. List Discovery Runs
    res_runs = client.get("/api/jobs/discovery-runs")
    assert res_runs.status_code == 200
    assert len(res_runs.json()) > 0

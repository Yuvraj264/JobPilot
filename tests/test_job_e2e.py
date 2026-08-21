import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.job import JobSource, RawJob, Job, JobDiscoveryRun
from app.services.adapters.mock import MockJobSourceAdapter
from app.services.job_discovery_service import JobDiscoveryService

client = TestClient(app)


def test_end_to_end_mock_job_discovery_pipeline():
    """
    Complete End-to-End Verification Test (Requirement 30):
    MockJobSourceAdapter -> JobDiscoveryService -> RawJob -> JobNormalizer -> JobDeduplicator -> PostgreSQL -> GET /api/jobs
    """
    db = SessionLocal()
    try:
        # Step 1: Clean pre-existing test jobs for clean E2E isolation
        db.query(Job).delete()
        db.query(RawJob).delete()
        db.query(JobDiscoveryRun).delete()
        db.commit()

        # Step 2: Execute Discovery Run via Service
        mock_adapter = MockJobSourceAdapter()
        summary = JobDiscoveryService.run_discovery_for_source(db, mock_adapter, limit=20, page=1)
        assert summary["status"] in ["COMPLETED", "PARTIAL"]
        assert summary["jobs_discovered"] == 20

        # Step 3: Verify RawJob DB Persistence
        raw_count = db.query(RawJob).count()
        assert raw_count == 20

        # Step 4: Verify Normalized Job DB Persistence & Deduplication
        job_count = db.query(Job).count()
        assert job_count >= 15  # At least 15 valid normalized jobs created

        # Step 5: Query REST API endpoint GET /api/jobs
        api_res = client.get("/api/jobs")
        assert api_res.status_code == 200
        job_list = api_res.json()
        assert len(job_list) == job_count

        # Step 6: Verify Normalized Fields in API output
        first_job = job_list[0]
        assert "title" in first_job
        assert "company_name" in first_job
        assert "employment_type" in first_job
        assert "workplace_type" in first_job
        assert "normalized_location" in first_job

    finally:
        db.close()

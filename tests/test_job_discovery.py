import pytest
from app.database.connection import SessionLocal
from app.services.adapters.mock import MockJobSourceAdapter
from app.services.job_discovery_service import JobDiscoveryService


def test_job_discovery_pipeline_and_partial_failure():
    """Test discovery engine execution with Mock adapter and verify malformed entries do not crash run."""
    db = SessionLocal()
    try:
        from app.models.job import Job, RawJob, JobDiscoveryRun
        db.query(Job).delete()
        db.query(RawJob).delete()
        db.query(JobDiscoveryRun).delete()
        db.commit()

        mock_adapter = MockJobSourceAdapter()
        res = JobDiscoveryService.run_discovery_for_source(db, mock_adapter, limit=25, page=1)

        assert res["source"] == "mock"
        assert res["jobs_discovered"] == 20
        assert res["jobs_created"] >= 15
        assert res["duplicates"] >= 1  # MOCK-109 is duplicate of MOCK-101
        assert res["invalid_jobs"] == 1  # MOCK-119 is missing company name

    finally:
        db.close()

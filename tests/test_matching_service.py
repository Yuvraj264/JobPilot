import pytest
from app.database.connection import SessionLocal
from app.services.profile_service import ProfileService
from app.services.seed_service import seed_sample_profile
from app.services.adapters.mock import MockJobSourceAdapter
from app.services.job_discovery_service import JobDiscoveryService
from app.services.job_matching_service import JobMatchingService


def test_job_matching_service_single_and_batch():
    db = SessionLocal()
    try:
        # Seed profile and mock jobs
        profile = seed_sample_profile(db, user_id=1)
        mock_adapter = MockJobSourceAdapter()
        JobDiscoveryService.run_discovery_for_source(db, mock_adapter, limit=10, page=1)

        # Batch Run
        run_res = JobMatchingService.run_batch_matching(db, profile.id, limit=10)
        assert run_res.status in ["COMPLETED", "PARTIAL"]
        assert run_res.jobs_evaluated > 0

        # Stats
        stats = JobMatchingService.get_matching_stats(db, profile.id)
        assert stats["jobs_evaluated"] > 0
        assert stats["apply"] + stats["review"] + stats["skip"] == stats["jobs_evaluated"]

    finally:
        db.close()

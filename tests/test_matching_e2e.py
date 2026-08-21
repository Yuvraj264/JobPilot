import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.matching import JobMatch, MatchRun
from app.models.job import Job, RawJob, JobDiscoveryRun
from app.services.seed_service import seed_sample_profile
from app.services.adapters.mock import MockJobSourceAdapter
from app.services.job_discovery_service import JobDiscoveryService

client = TestClient(app)


def test_end_to_end_matching_pipeline():
    """
    Complete End-to-End Verification Test (Requirement 30):
    Mock Jobs (Phase 4) -> Profile (Phase 2) -> JobMatchingService -> Eligibility -> Skill/Role/Location -> Score -> Recommendation -> Explanation -> DB -> API
    """
    db = SessionLocal()
    try:
        # Step 1: Clean pre-existing test data
        db.query(JobMatch).delete()
        db.query(MatchRun).delete()
        db.commit()

        # Step 2: Seed Profile & Discovered Mock Jobs
        profile = seed_sample_profile(db, user_id=1)
        mock_adapter = MockJobSourceAdapter()
        JobDiscoveryService.run_discovery_for_source(db, mock_adapter, limit=20, page=1)

        # Step 3: Execute Batch Matching Run via API
        run_res = client.post("/api/matching/run", json={"limit": 20})
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert run_data["jobs_evaluated"] > 0
        assert run_data["status"] in ["COMPLETED", "PARTIAL"]

        # Step 4: Verify Database Persistence
        db_matches = db.query(JobMatch).filter(JobMatch.profile_id == profile.id).all()
        assert len(db_matches) == run_data["jobs_evaluated"]

        # Step 5: Query Matches REST API Endpoint GET /api/matching/jobs
        api_res = client.get("/api/matching/jobs?limit=50")
        assert api_res.status_code == 200
        matches_list = api_res.json()
        assert len(matches_list) == len(db_matches)

        # Step 6: Verify Structured Component Output & Explanations
        first_match = matches_list[0]
        assert "overall_score" in first_match
        assert first_match["recommendation"] in ["APPLY", "REVIEW", "SKIP"]
        assert "skills" in first_match["component_scores"]
        assert "explanation" in first_match
        assert "summary" in first_match["explanation"]
        assert "strengths" in first_match["explanation"]
        assert "concerns" in first_match["explanation"]

    finally:
        db.close()

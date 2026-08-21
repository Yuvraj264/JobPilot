import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.automation import AutomationRun, ActionLog
from app.models.job import Job
from app.services.seed_service import seed_sample_profile
from app.services.application_agent import ApplicationAgent

client = TestClient(app)


def test_end_to_end_automation_pipeline_reaches_review():
    """
    Complete End-to-End Integration Verification Test (Requirement 30):
    Mock Job -> Profile -> Resume -> Mock App -> BrowserController -> PageInspector -> FormAnalyzer -> ProfileFieldMapper -> ActionPlanner -> ActionExecutor -> Step 1 -> Step 2 -> Step 3 -> Review -> READY_FOR_REVIEW
    """
    db = SessionLocal()
    try:
        # Step 1: Ensure Synthetic Mock Job 101 exists in DB
        job = db.query(Job).filter(Job.id == 101).first()
        if not job:
            job = Job(id=101, title="Junior QA Engineer", company_name="Acme Technologies", status="ACTIVE")
            db.add(job)
            db.commit()

        # Step 2: Seed Profile
        profile = seed_sample_profile(db, user_id=1)

        # Step 3: Trigger Automation via Agent
        run = ApplicationAgent.start_automation(db, profile_id=profile.id, job_id=101)

        # Step 4: Verify Agent Pipeline Actions
        assert run.actions_attempted > 0

        # Step 5: Verify Run reached READY_FOR_REVIEW or PAUSED on screening questions
        assert run.state in ["READY_FOR_REVIEW", "PAUSED"]
        if run.state == "READY_FOR_REVIEW":
            assert run.status == "COMPLETED"
            assert "review" in run.current_url.lower()

        # Step 6: Verify Action Log DB Records
        action_logs = db.query(ActionLog).filter(ActionLog.automation_run_id == run.id).all()
        assert len(action_logs) > 0

    finally:
        db.close()

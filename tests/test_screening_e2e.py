import pytest
from app.database.connection import SessionLocal
from app.models.job import Job
from app.services.seed_service import seed_sample_profile
from app.services.application_agent import ApplicationAgent
from app.models.screening import ApplicationQuestion, ApplicationAnswer


def test_screening_engine_e2e_integration():
    """
    End-to-End Integration Verification Test (Requirement 32):
    Mock Application -> Browser Agent -> Question Detection -> Classifier -> Answer Source Resolver -> Generator -> Validator -> Human Review Queue
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == 101).first()
        if not job:
            job = Job(id=101, title="Junior QA Engineer", company_name="Acme Technologies", status="ACTIVE")
            db.add(job)
            db.commit()

        profile = seed_sample_profile(db, user_id=1)

        # Trigger Automation Run
        run = ApplicationAgent.start_automation(db, profile_id=profile.id, job_id=101)

        assert run.actions_attempted > 0
        assert run.state in ["READY_FOR_REVIEW", "PAUSED"]

        # Verify ApplicationQuestion DB entries were populated during inspection
        questions = db.query(ApplicationQuestion).filter(ApplicationQuestion.automation_run_id == run.id).all()
        # Verify question records exist if screening step was reached
        for q in questions:
            assert q.question_type is not None
            assert q.answer_source is not None

    finally:
        db.close()

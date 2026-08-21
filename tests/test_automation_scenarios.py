import time
import pytest
from app.database.connection import SessionLocal
from app.models.profile import User, UserProfile, Education, JobPreference
from app.services.seed_service import seed_sample_profile
from app.services.application_agent import ApplicationAgent
from app.models.job import Job


def test_mock_scenarios():
    db = SessionLocal()
    try:
        # Ensure job 101 exists in DB
        job = db.query(Job).filter(Job.id == 101).first()
        if not job:
            job = Job(id=101, title="Junior QA Engineer", company_name="Acme Technologies", status="ACTIVE")
            db.add(job)
            db.commit()

        # Scenario 1: Normal Flow -> Reaches READY_FOR_REVIEW or PAUSED on screening questions
        profile = seed_sample_profile(db, user_id=1)
        run1 = ApplicationAgent.start_automation(db, profile_id=profile.id, job_id=101)
        assert run1.state in ["READY_FOR_REVIEW", "PAUSED"]
        assert run1.actions_attempted > 0

        # Scenario 2: Missing Phone Number -> Agent Pauses Safely
        unique_email = f"nophone.user.{int(time.time()*1000)}@example.com"
        user_no_phone = User(email=unique_email)
        db.add(user_no_phone)
        db.commit()
        db.refresh(user_no_phone)

        profile_no_phone = UserProfile(
            user_id=user_no_phone.id,
            full_name="No Phone User",
            email=unique_email,
            phone=None,
            current_city="Bangalore",
            current_country="India",
            current_role="QA Analyst",
            years_of_experience=2.0
        )
        db.add(profile_no_phone)
        db.commit()
        db.refresh(profile_no_phone)

        run2 = ApplicationAgent.start_automation(db, profile_id=profile_no_phone.id, job_id=101)
        assert run2.state == "PAUSED"
        assert run2.human_intervention_required is True
        assert "missing" in run2.pause_reason.lower() or "phone" in run2.pause_reason.lower() or "mobile" in run2.pause_reason.lower()

    finally:
        db.close()

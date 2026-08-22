import pytest
from sqlalchemy.orm import Session
from app.models.profile import User, UserProfile, Skill
from app.models.job import Job
from app.models.matching import MatchConfig
from app.services.matching.scoring_engine import ScoringEngine
from app.database.connection import SessionLocal

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

def test_phase_01_to_05_regression(db: Session):
    """
    Verifies base profile setup, matching configurations, and core scoring capabilities.
    """
    # Clear existing if any from previous failed runs
    db.query(UserProfile).filter(UserProfile.email == "test_regress_1@example.com").delete()
    db.query(User).filter(User.email == "test_regress_1@example.com").delete()
    db.commit()

    # 1. Profile Setup
    user = User(email="test_regress_1@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Tester Bob",
        email="test_regress_1@example.com",
        years_of_experience=3.0,
        current_role="QA Automation"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    skill1 = Skill(profile_id=profile.id, name="Python", proficiency="Expert", years_of_experience=3.0)
    skill2 = Skill(profile_id=profile.id, name="Selenium", proficiency="Intermediate", years_of_experience=2.0)
    db.add(skill1)
    db.add(skill2)
    db.commit()

    # 2. Matching Engine Weights Setup
    config = MatchConfig(
        profile_id=profile.id,
        weight_skills=0.40,
        weight_role=0.30,
        weight_experience=0.30,
        weight_location=0.0,
        weight_workplace=0.0,
        weight_employment=0.0,
        weight_education=0.0,
        weight_semantic=0.0,
        threshold_apply=80.0,
        threshold_review=60.0
    )
    db.add(config)
    db.commit()

    # 3. Create mock job
    job = Job(
        title="QA Automation Engineer",
        company_name="Regression Inc",
        location="Austin, TX",
        description="Must have skills: Python, Selenium. 3+ years experience required.",
        experience_min=3,
        experience_max=5
    )
    db.add(job)
    db.commit()

    # 4. Run Matching evaluation
    match_eval = ScoringEngine.evaluate_job(profile, job, config)
    
    assert match_eval["eligible"] is True
    assert match_eval["overall_score"] >= 80.0
    assert match_eval["recommendation"] == "APPLY"
    assert "Python" in match_eval["strengths"][0]

    # Clean up
    db.delete(config)
    db.delete(profile)
    db.delete(user)
    db.delete(job)
    db.commit()

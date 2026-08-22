import pytest
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models import User, UserProfile, Job, Skill, Project, Certification
from app.models.personalization import (
    PersonalPreferenceProfile,
    PreferenceConfigurationVersion,
    BehavioralSignal,
    JobFeedback,
    OptimizationSuggestion,
    OutcomeFeedback
)
from app.models.matching import MatchConfig
from app.services.matching.scoring_engine import ScoringEngine
from app.services.personalization.preference_inference import (
    get_or_create_preference_profile,
    log_config_version,
    rollback_preference_config,
    PreferenceInferenceService
)
from app.services.personalization.optimization_service import OptimizationSuggestionService
from app.services.personalization.recommendation_diversifier import RecommendationDiversifier


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="module", autouse=True)
def clean_db():
    session = SessionLocal()
    try:
        emails = [
            "test_pref_defaults@example.com",
            "test_rollback@example.com",
            "test_inference@example.com",
            "test_personalize_score@example.com",
            "test_skill_evidence@example.com"
        ]
        for i in range(20):
            emails.append(f"synth_user_{i}@example.com")
            
        for email in emails:
            session.query(UserProfile).filter(UserProfile.email == email).delete()
            session.query(User).filter(User.email == email).delete()
        session.commit()
        
        # Reset primary key sequences to prevent postgres key violations
        session.execute(text("SELECT setval('users_id_seq', COALESCE((SELECT MAX(id)+1 FROM users), 1), false);"))
        session.execute(text("SELECT setval('user_profiles_id_seq', COALESCE((SELECT MAX(id)+1 FROM user_profiles), 1), false);"))
        session.commit()
    finally:
        session.close()


def test_preference_profile_creation_and_defaults(db: Session):
    # Setup temp user
    user = User(email="test_pref_defaults@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Alex Preference",
        email="test_pref_defaults@example.com",
        years_of_experience=5.0
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # 1. Test get_or_create_preference_profile defaults
    pref = get_or_create_preference_profile(db, profile.id)
    assert pref is not None
    assert pref.enabled is True
    assert pref.answer_style == "Concise"
    assert len(pref.preferred_roles) == 0

    # Clean up
    db.delete(pref)
    db.delete(profile)
    db.delete(user)
    db.commit()


def test_config_versioning_and_rollback(db: Session):
    user = User(email="test_rollback@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Alex Rollback",
        email="test_rollback@example.com"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    pref = get_or_create_preference_profile(db, profile.id)
    
    # Update preference explicitly & version it
    pref.preferred_roles = [{"value": "SDET", "source": "USER_EXPLICIT", "strength": 1.0}]
    log_config_version(db, profile.id, {"preferred_roles": "added SDET"})
    
    latest_v = db.query(PreferenceConfigurationVersion).filter(
        PreferenceConfigurationVersion.profile_id == profile.id
    ).order_by(PreferenceConfigurationVersion.version.desc()).first()
    assert latest_v is not None
    assert latest_v.version == 1
    assert latest_v.preferences_snapshot["preferred_roles"][0]["value"] == "SDET"

    # Rollback configuration
    success = rollback_preference_config(db, profile.id)
    assert success is True
    
    # Reload preferences profile
    db.refresh(pref)
    assert len(pref.preferred_roles) == 0  # Restored to default empty list

    # Clean up
    db.delete(pref)
    db.delete(profile)
    db.delete(user)
    db.commit()


def test_preference_inference_and_suggestions(db: Session):
    user = User(email="test_inference@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Alex Inference",
        email="test_inference@example.com"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Seed jobs
    job1 = Job(title="QA Automation Engineer", company_name="Test Inc", description="Selenium, Python")
    job2 = Job(title="QA Automation Engineer", company_name="Demo Inc", description="Cypress, Javascript")
    job3 = Job(title="QA Automation Engineer", company_name="Extractor Inc", description="Playwright, Python")
    db.add_all([job1, job2, job3])
    db.commit()

    # Record saved job feedbacks
    f1 = JobFeedback(profile_id=profile.id, job_id=job1.id, feedback_type="Save")
    f2 = JobFeedback(profile_id=profile.id, job_id=job2.id, feedback_type="Save")
    f3 = JobFeedback(profile_id=profile.id, job_id=job3.id, feedback_type="Save")
    db.add_all([f1, f2, f3])
    db.commit()

    # Run inference generator
    suggestions = PreferenceInferenceService.generate_suggestions(db, profile.id)
    assert len(suggestions) > 0
    sug = suggestions[0]
    assert sug.category == "role"
    assert "QA Automation" in sug.suggestion

    # Accept suggestion
    success = PreferenceInferenceService.accept_suggestion(db, sug.id)
    assert success is True

    # Verify preference profile updated
    pref = get_or_create_preference_profile(db, profile.id)
    assert len(pref.preferred_roles) > 0
    assert pref.preferred_roles[0]["value"] == "QA Automation"

    # Clean up
    db.delete(pref)
    db.delete(f1)
    db.delete(f2)
    db.delete(f3)
    db.delete(job1)
    db.delete(job2)
    db.delete(job3)
    db.delete(sug)
    db.delete(profile)
    db.delete(user)
    db.commit()


def test_scoring_personalization_adjustment(db: Session):
    user = User(email="test_personalize_score@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Alex Scoring",
        email="test_personalize_score@example.com"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    s1 = Skill(profile_id=profile.id, name="Python", category="Programming")
    db.add(s1)
    db.commit()

    config = MatchConfig(
        profile_id=profile.id,
        weight_skills=1.0,
        weight_role=0.0,
        weight_experience=0.0,
        weight_location=0.0,
        weight_workplace=0.0,
        weight_employment=0.0,
        weight_education=0.0,
        weight_semantic=0.0
    )
    db.add(config)
    db.commit()

    job = Job(title="QA Automation Engineer", company_name="Quality Corp", description="Python test code details.")
    db.add(job)
    db.commit()

    # Base match evaluation (no preference profile configured yet)
    match_eval_base = ScoringEngine.evaluate_job(profile, job, config)
    base_score = match_eval_base["overall_score"]

    # Configure PersonalPreferenceProfile
    pref = get_or_create_preference_profile(db, profile.id)
    pref.preferred_roles = [{"value": "QA Automation", "source": "USER_EXPLICIT", "strength": 1.0}]
    db.commit()

    # Re-evaluate matching with personalization ON
    match_eval_pers = ScoringEngine.evaluate_job(profile, job, config)
    personalized_score = match_eval_pers["overall_score"]
    
    # Personalized score should have a positive adjustment factor because of matching role preference!
    assert personalized_score > base_score
    assert match_eval_pers["explanation"]["preference_fit"] > 0

    # Clean up
    db.delete(pref)
    db.delete(config)
    db.delete(job)
    db.delete(s1)
    db.delete(profile)
    db.delete(user)
    db.commit()


def test_skill_evidence_grounding_rules(db: Session):
    user = User(email="test_skill_evidence@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Alex Skills",
        email="test_skill_evidence@example.com"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # 1. Add skill to profile list
    s1 = Skill(profile_id=profile.id, name="Selenium", category="Testing")
    db.add(s1)
    db.commit()

    # Check evidence for Selenium (must be supported)
    ev_selenium = OptimizationSuggestionService.get_skill_evidence(db, profile.id, "Selenium")
    assert ev_selenium["supported"] is True
    assert "USER_PROFILE" in ev_selenium["sources"]

    # Check evidence for nonexistent skill (must NOT be supported)
    ev_aws = OptimizationSuggestionService.get_skill_evidence(db, profile.id, "AWS")
    assert ev_aws["supported"] is False

    # Clean up
    db.delete(s1)
    db.delete(profile)
    db.delete(user)
    db.commit()


def test_recommendation_diversification(db: Session):
    job1 = Job(id=101, title="QA Automation Engineer", company_name="Company A", location="Remote")
    job2 = Job(id=102, title="QA Automation Engineer", company_name="Company A", location="Remote")
    job3 = Job(id=103, title="SDET", company_name="Company B", location="Austin")

    matches = [
        {"overall_score": 90.0, "job": job1},
        {"overall_score": 88.0, "job": job2},  # Same company, duplicate title
        {"overall_score": 85.0, "job": job3}
    ]

    diversified = RecommendationDiversifier.diversify(matches, limit=2)
    assert len(diversified) == 2
    # The top diversified results should prioritize Company A (job1) and Company B (job3),
    # deferring the duplicate company listing (job2)!
    companies = [m["job"].company_name for m in diversified]
    assert "Company A" in companies
    assert "Company B" in companies


def test_synthetic_20_users_benchmark(db: Session):
    """
    Creates multiple synthetic profiles and validates score diversity.
    """
    users = []
    profiles = []
    prefs = []

    # Create 20 synthetic profiles
    for i in range(20):
        email = f"synth_user_{i}@example.com"
        u = User(email=email)
        db.add(u)
        db.commit()
        users.append(u)

        p = UserProfile(user_id=u.id, full_name=f"User {i}", email=email)
        db.add(p)
        db.commit()
        db.refresh(p)
        profiles.append(p)

        pref = get_or_create_preference_profile(db, p.id)
        # Alternate preferences
        if i % 3 == 0:
            pref.preferred_roles = [{"value": "QA Automation", "source": "USER_EXPLICIT", "strength": 1.0}]
        elif i % 3 == 1:
            pref.preferred_roles = [{"value": "Backend", "source": "USER_EXPLICIT", "strength": 1.0}]
        else:
            pref.preferred_roles = [{"value": "SDET", "source": "USER_EXPLICIT", "strength": 1.0}]
        prefs.append(pref)
    
    db.commit()

    # Evaluate matching for a specific mock job
    job = Job(title="QA Automation Engineer", company_name="Quality Inc")
    db.add(job)
    db.commit()

    config = MatchConfig(
        profile_id=profiles[0].id,  # dummy config
        weight_skills=0.0,
        weight_role=1.0,
        weight_experience=0.0,
        weight_location=0.0,
        weight_workplace=0.0,
        weight_employment=0.0,
        weight_education=0.0,
        weight_semantic=0.0
    )
    db.add(config)
    db.commit()

    # Evaluate scores for all 20 users
    scores = []
    for p in profiles:
        res = ScoringEngine.evaluate_job(p, job, config)
        scores.append(res["overall_score"])

    # Users with QA Automation preference should have higher scores than users with Backend preference!
    # Let's verify score diversity exists
    assert len(set(scores)) > 1

    # Cleanup synthetic benchmark
    db.delete(job)
    db.delete(config)
    for pref in prefs:
        db.delete(pref)
    for p in profiles:
        db.delete(p)
    for u in users:
        db.delete(u)
    db.commit()

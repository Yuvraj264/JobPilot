import pytest
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models import User, UserProfile, Job, Skill
from app.models.mission import JobSearchMission, MissionRun, MissionAuditLog
from app.models.matching import MatchConfig, JobMatch
from app.models.application import Application, ApplicationQueue, SubmissionAuthorization
from app.models.personalization import PersonalPreferenceProfile
from app.services.mission_engine import MissionEngine
from app.services.orchestration.orchestrator import JobPilotOrchestrator


@pytest.fixture(scope="function")
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="module", autouse=True)
def recreate_db():
    from app.database.connection import engine
    from app.database.connection import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    session = SessionLocal()
    try:
        # Delete existing test users
        emails = [
            "mission_test_user@example.com",
            "mission_adversarial@example.com",
            "mission_exp@example.com"
        ]
        for i in range(10):
            emails.append(f"synth_mission_{i}@example.com")
            
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


def test_mission_creation_and_validation(db: Session):
    # Setup test profile
    user = User(email="mission_test_user@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Alex Mission",
        email="mission_test_user@example.com"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Initialize personal preference profile (remote only)
    pref = PersonalPreferenceProfile(
        profile_id=profile.id,
        enabled=True,
        workplace_modes=[{"value": "REMOTE", "type": "preferred"}, {"value": "ONSITE", "type": "disliked"}]
    )
    db.add(pref)
    db.commit()

    # Create mission configuration (onsite target to trigger warning conflict)
    mission = JobSearchMission(
        profile_id=profile.id,
        name="QA Bangalore Onsite",
        status="DRAFT",
        objective={
            "target_roles": ["QA Automation"],
            "target_locations": ["Bangalore"],
            "target_work_modes": ["ONSITE"],
            "minimum_match_score": 75.0
        },
        limits={"max_applications_per_day": 3},
        scheduler_preset={"schedule_type": "daily"}
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)

    # Validate mission configuration
    val = MissionEngine.validate_configuration(db, mission)
    assert val["valid"] is True
    # Verification warnings - conflicts REMOTE-only vs ONSITE-only
    assert len(val["warnings"]) > 0
    assert "Global preference is Remote-only but Mission specifies Onsite" in val["warnings"][0]

    # Clean up
    db.delete(mission)
    db.delete(pref)
    db.delete(profile)
    db.delete(user)
    db.commit()


def test_mission_auditing_and_rollback(db: Session):
    user = User(email="mission_test_user@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Alex Mission Audit",
        email="mission_test_user@example.com"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    mission = JobSearchMission(
        profile_id=profile.id,
        name="SDET Bangalore Campaign",
        status="DRAFT",
        objective={
            "target_roles": ["SDET"],
            "minimum_match_score": 80.0
        },
        limits={"max_applications_per_day": 3}
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)

    # Update config and log audit
    old_cfg = {"name": mission.name, "objective": mission.objective}
    new_obj = {"target_roles": ["SDET"], "minimum_match_score": 85.0}
    mission.objective = new_obj
    mission.configuration_version = 2
    
    MissionEngine.log_audit(db, mission.id, old_cfg, {"name": mission.name, "objective": new_obj}, 2)
    db.commit()

    # Query audit logs
    audit = db.query(MissionAuditLog).filter(MissionAuditLog.mission_id == mission.id).first()
    assert audit is not None
    assert audit.configuration_version == 2
    assert audit.changes["objective"]["new"]["minimum_match_score"] == 85.0

    # Clean up
    db.delete(audit)
    db.delete(mission)
    db.delete(profile)
    db.delete(user)
    db.commit()


def test_mission_run_execution(db: Session):
    user = User(email="mission_test_user@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Alex Mission Execution",
        email="mission_test_user@example.com",
        years_of_experience=3.0,
        current_role="QA Automation"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Seed matching skills
    s1 = Skill(profile_id=profile.id, name="Selenium", category="Testing")
    s2 = Skill(profile_id=profile.id, name="Python", category="Testing")
    db.add_all([s1, s2])
    db.commit()

    # Seed default resume
    from app.models.resume import Resume
    resume = Resume(
        profile_id=profile.id,
        name="Default Resume",
        original_filename="resume.pdf",
        file_path="/tmp/resume.pdf",
        file_type="PDF",
        file_size=1024,
        is_default=True,
        raw_text="Experienced QA Automation",
        processing_status="PROCESSED"
    )
    db.add(resume)
    db.commit()

    job = Job(
        title="QA Automation Engineer",
        company_name="TestCorp",
        location="Bangalore",
        description="Python test engineer Selenium",
        status="ACTIVE",
        job_url="http://example.com/job"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Seed match config & match run score
    match = JobMatch(profile_id=profile.id, job_id=job.id, overall_score=85.0, recommendation="APPLY", eligible=True)
    db.add(match)
    db.commit()

    mission = JobSearchMission(
        profile_id=profile.id,
        name="Active QA Campaign",
        status="ACTIVE",
        objective={
            "target_roles": ["QA Automation"],
            "target_locations": ["Bangalore"],
            "preferred_skills": ["Selenium"],
            "minimum_match_score": 80.0
        },
        limits={"max_applications_per_day": 2, "max_applications_per_run": 2},
        application_strategy="HUMAN_REVIEW"
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)

    # Execute mission run
    run = MissionEngine.run_mission(db, mission.id, "MANUAL")
    assert run.status == "COMPLETED"
    assert run.jobs_selected == 1
    assert run.applications_prepared == 1

    # Verify Application generated primary mission ID attribution
    app = db.query(Application).filter(Application.job_id == job.id).first()
    assert app is not None
    assert app.primary_mission_id == mission.id
    assert app.status == "READY_FOR_REVIEW"

    # Clean up
    db.delete(app)
    db.delete(run)
    db.delete(mission)
    db.delete(match)
    db.delete(job)
    db.delete(s1)
    db.delete(s2)
    db.delete(resume)
    db.delete(profile)
    db.delete(user)
    db.commit()


def test_mission_exclusions(db: Session):
    # If job has excluded keyword/company, it should filter it out
    job = Job(title="Senior QA Automation Engineer", company_name="BlacklistCorp", location="Bangalore")
    mission = JobSearchMission(
        objective={
            "target_roles": ["QA Automation"],
            "excluded_companies": ["BlacklistCorp"]
        }
    )
    fit = MissionEngine.calculate_mission_fit(job, mission)
    assert fit["fit"] is False
    assert "Excluded company name matched" in fit["explanation"][0]


def test_mission_expiration(db: Session):
    user = User(email="mission_exp@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Alex Exp",
        email="mission_exp@example.com"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Ended yesterday
    yesterday = datetime.now() - timedelta(days=1)
    mission = JobSearchMission(
        profile_id=profile.id,
        name="Expired Mission",
        status="ACTIVE",
        end_date=yesterday,
        objective={"target_roles": ["QA"]}
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)

    run = MissionEngine.run_mission(db, mission.id)
    assert run.status == "FAILED"
    assert "expired" in run.errors[0]
    
    db.refresh(mission)
    assert mission.status == "EXPIRED"

    # Clean up
    db.delete(run)
    db.delete(mission)
    db.delete(profile)
    db.delete(user)
    db.commit()


def test_adversarial_limits_enforcement(db: Session):
    user = User(email="mission_adversarial@example.com")
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        full_name="Alex Limits",
        email="mission_adversarial@example.com"
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Get default global config
    global_config = JobPilotOrchestrator.get_or_create_config(db, profile.id)
    global_config.max_applications_per_day = 10
    db.commit()

    # Mission configured to request 100 applications/day (adversarial)
    mission = JobSearchMission(
        profile_id=profile.id,
        name="Greedy Mission",
        status="ACTIVE",
        limits={"max_applications_per_day": 100}
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)

    val = MissionEngine.validate_configuration(db, mission)
    assert val["valid"] is False
    assert "cannot exceed global daily limit" in val["errors"][0]

    # Clean up
    db.delete(mission)
    db.delete(global_config)
    db.delete(profile)
    db.delete(user)
    db.commit()


def test_10_synthetic_missions_scenarios(db: Session):
    """
    Spawns 10 synthetic missions and verifies fit classifications.
    """
    job = Job(title="QA Automation Engineer", company_name="Google", location="Bangalore", description="Python test Selenium SQL")
    
    scenarios = [
        {"roles": ["QA Automation"], "locs": ["Bangalore"], "expected_fit": True},
        {"roles": ["SDET"], "locs": ["Bangalore"], "expected_fit": False},
        {"roles": ["QA Automation"], "locs": ["Remote"], "expected_fit": False},
        {"roles": ["Backend"], "locs": ["Delhi"], "expected_fit": False},
        {"roles": ["QA Automation"], "locs": ["Pune"], "expected_fit": False},
        {"roles": ["QA"], "locs": ["Bangalore"], "expected_fit": True},
        {"roles": ["Manager"], "locs": ["Bangalore"], "expected_fit": False},
        {"roles": ["Developer"], "locs": ["Chennai"], "expected_fit": False},
        {"roles": ["QA Automation"], "locs": ["Bangalore"], "expected_fit": True},
        {"roles": ["Automation"], "locs": ["Bangalore"], "expected_fit": True}
    ]

    for i, scen in enumerate(scenarios):
        email = f"synth_mission_{i}@example.com"
        u = User(email=email)
        db.add(u)
        db.commit()

        p = UserProfile(user_id=u.id, full_name=f"Synth Candidate {i}", email=email)
        db.add(p)
        db.commit()
        db.refresh(p)

        mission = JobSearchMission(
            profile_id=p.id,
            name=f"Synth Mission {i}",
            objective={
                "target_roles": scen["roles"],
                "target_locations": scen["locs"]
            }
        )
        db.add(mission)
        db.commit()

        fit = MissionEngine.calculate_mission_fit(job, mission)
        assert fit["fit"] is scen["expected_fit"]

        # Cleanup
        db.delete(mission)
        db.delete(p)
        db.delete(u)
        db.commit()

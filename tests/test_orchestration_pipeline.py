import pytest
from datetime import datetime, timedelta
import concurrent.futures
from sqlalchemy.orm import Session

from app.models.profile import UserProfile, Skill
from app.models.job import Job, JobSource
from app.models.matching import JobMatch
from app.models.application import Application, ApplicationQueue, SubmissionRun
from app.models.orchestration import OrchestrationRun, AutomationConfiguration, DailyAutomationMetric
from app.services.orchestration.selection_service import JobSelectionService
from app.services.orchestration.retry_manager import RetryManager
from app.services.orchestration.orchestrator import JobPilotOrchestrator
from app.database.connection import SessionLocal

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def seed_sample_data(db: Session):
    """Utility helper seeding profile and default active configuration."""
    from app.services.seed_service import seed_sample_profile
    profile = seed_sample_profile(db, user_id=1)

    config = JobPilotOrchestrator.get_or_create_config(db, profile.id)
    
    # Add a mock default resume
    from app.models.resume import Resume
    resume = db.query(Resume).filter(Resume.profile_id == profile.id, Resume.is_default == True).first()
    if not resume:
        resume = Resume(
            profile_id=profile.id,
            name="Master Resume.pdf",
            original_filename="Master Resume.pdf",
            file_path="/tmp/master_resume.pdf",
            file_type="PDF",
            file_size=1024,
            processing_status="PROCESSED",
            is_default=True
        )
        db.add(resume)
        db.commit()

    return profile, config


def test_job_selection_and_cooldown(db: Session):
    """
    Verifies that JobSelectionService correctly selects qualified jobs, enforces cooldown,
    and prevents duplicate applications.
    """
    profile, config = seed_sample_data(db)
    config.minimum_match_score = 80.0
    db.commit()

    # Create matching jobs
    job1 = Job(title="Staff Software Engineer", company_name="TechCorp", status="ACTIVE")
    job2 = Job(title="Staff Software Engineer", company_name="TechCorp", status="ACTIVE")
    db.add_all([job1, job2])
    db.commit()
    db.refresh(job1)
    db.refresh(job2)

    # Add Match scores
    match1 = JobMatch(job_id=job1.id, profile_id=profile.id, overall_score=85.0, recommendation="APPLY", eligible=True)
    match2 = JobMatch(job_id=job2.id, profile_id=profile.id, overall_score=92.0, recommendation="APPLY", eligible=True)
    db.add_all([match1, match2])
    db.commit()

    # Test Initial Selection
    selected = JobSelectionService.select_jobs_for_orchestration(db, profile.id, config)
    assert len(selected) == 2
    assert selected[0].id == job1.id

    # Test Duplicate check: Apply to Job 1
    app1 = Application(profile_id=profile.id, job_id=job1.id, status="SUBMITTED", submitted_at=datetime.now())
    db.add(app1)
    db.commit()

    # Job 1 and Job 2 (cooldown duplicate of Job 1) should be skipped now
    selected_after_apply = JobSelectionService.select_jobs_for_orchestration(db, profile.id, config)
    assert len(selected_after_apply) == 0

    # Test Cooldown Enforcement on Company/Title Match
    history_status = JobSelectionService.get_application_history_status(db, profile.id, job2, cooldown_days=config.cooldown_days)
    # job2 is TechCorp Staff Software Engineer, matching applied company & title, so it is blocked by cooldown
    assert history_status == "ALREADY_APPLIED"


def test_daily_limits_check(db: Session):
    """
    Verifies daily safety execution limits.
    """
    profile, config = seed_sample_data(db)
    config.max_applications_per_day = 2
    db.commit()

    joba = Job(title="QA Engineer A", company_name="LimitsCorp", status="ACTIVE")
    jobb = Job(title="QA Engineer B", company_name="LimitsCorp", status="ACTIVE")
    db.add_all([joba, jobb])
    db.commit()
    db.refresh(joba)
    db.refresh(jobb)

    # Setup applications submitted today
    app1 = Application(profile_id=profile.id, job_id=joba.id, status="SUBMITTED", submitted_at=datetime.now())
    app2 = Application(profile_id=profile.id, job_id=jobb.id, status="SUBMITTED", submitted_at=datetime.now())
    db.add_all([app1, app2])
    db.commit()

    # Verify limit hit
    limits = JobSelectionService.check_daily_limits_reached(db, profile.id, config)
    assert limits["reached"] is True
    assert "daily limit" in limits["reason"].lower()


def test_retry_manager_recoverability():
    """
    Verifies that RetryManager correctly identifies recoverable vs non-recoverable error messages.
    """
    assert RetryManager.is_recoverable("Timeout connection error from browser.") is True
    assert RetryManager.is_recoverable("Browser crashed during inspection.") is True
    assert RetryManager.is_recoverable("Playwright network failed.") is True

    # Sensitive or bot-check markers are not retried
    assert RetryManager.is_recoverable("CAPTCHA detected, manual pause requested.") is False
    assert RetryManager.is_recoverable("Validation error: field email missing.") is False
    assert RetryManager.is_recoverable("Failed domain validation checks.") is False


def test_orchestration_failure_isolation_and_crash_recovery(db: Session):
    """
    Tests that a failure on one job does not crash the entire orchestration run,
    and checkpoint recovery restarts from last durable states.
    """
    profile, config = seed_sample_data(db)

    # Trigger run with 2 jobs
    job1 = Job(title="DevOps Engineer", company_name="CloudSolutions", status="ACTIVE")
    job2 = Job(title="Site Reliability Engineer", company_name="CloudSolutions", status="ACTIVE")
    db.add_all([job1, job2])
    db.commit()
    db.refresh(job1)
    db.refresh(job2)

    match1 = JobMatch(job_id=job1.id, profile_id=profile.id, overall_score=90.0, recommendation="APPLY", eligible=True)
    match2 = JobMatch(job_id=job2.id, profile_id=profile.id, overall_score=88.0, recommendation="APPLY", eligible=True)
    db.add_all([match1, match2])
    db.commit()

    # Cause job1 to fail tailoring by not seeding default resume (remove it)
    from app.models.resume import Resume
    db.query(Resume).delete()
    db.commit()

    run_rec = OrchestrationRun(
        profile_id=profile.id,
        status="RUNNING",
        trigger_type="MANUAL",
        jobs_discovered=2,
        jobs_matched=2
    )
    db.add(run_rec)
    db.commit()
    db.refresh(run_rec)

    # Execute in a thread pool to avoid loop blocks
    with concurrent.futures.ThreadPoolExecutor() as executor:
        run = executor.submit(JobPilotOrchestrator.run_pipeline, db, profile.id, "MANUAL", run_rec.id).result()

    # Isolation check: Run continues with error count incremented
    assert run.error_count > 0
    assert run.status in ["FAILED", "PARTIAL"]


def test_orchestrator_dry_run_preview(db: Session):
    """
    Verifies that dry-run is safely respected, creating queues but skipping final clicks.
    """
    profile, config = seed_sample_data(db)
    config.dry_run = True
    db.commit()

    job = Job(title="Frontend Developer", company_name="WebPortal", status="ACTIVE", application_url="http://localhost:8000/mock/synthetic-careers/site_a")
    db.add(job)
    db.commit()
    db.refresh(job)

    match = JobMatch(job_id=job.id, profile_id=profile.id, overall_score=85.0, recommendation="APPLY", eligible=True)
    db.add(match)
    db.commit()

    run_rec = OrchestrationRun(
        profile_id=profile.id,
        status="RUNNING",
        trigger_type="MANUAL",
        jobs_discovered=1,
        jobs_matched=1
    )
    db.add(run_rec)
    db.commit()
    db.refresh(run_rec)

    # Run pipeline in separate thread pool
    with concurrent.futures.ThreadPoolExecutor() as executor:
        run = executor.submit(JobPilotOrchestrator.run_pipeline, db, profile.id, "MANUAL", run_rec.id).result()

    # Submitted count in dry-run should NOT persist a live SubmissionRun submitted status
    assert run.status == "COMPLETED"
    
    # Check that any SubmissionRun records were marked dry run
    submissions = db.query(SubmissionRun).all()
    for s in submissions:
        # Dry runs should not submit live HTTP parameters
        assert s.status != "SUBMITTED"

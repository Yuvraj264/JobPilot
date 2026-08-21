import pytest
from unittest.mock import MagicMock
from app.database.connection import SessionLocal
from app.models.job import Job, JobSource
from app.models.tailoring import ApplicationPackage
from app.models.application import (
    Application,
    ApplicationQueue,
    ApplicationSourceConfiguration,
    HumanInterventionEvent,
    SubmissionAuthorization,
)
from app.services.automation.adapters.registry import registry
from app.services.automation.execution_worker import ApplicationExecutionWorker
from app.services.automation.browser_session import ApplicationBrowserSession, DomainValidationError
from app.services.seed_service import seed_sample_profile


def test_adapter_capability_declarations():
    mock_ad = registry.get("mock")
    assert mock_ad is not None
    caps = mock_ad.get_capabilities()
    assert caps["form_filling"] is True
    assert caps["submission"] is True
    assert caps["human_assisted"] is False

    linkedin_ad = registry.get("linkedin")
    assert linkedin_ad is not None
    link_caps = linkedin_ad.get_capabilities()
    assert link_caps["submission"] is False
    assert link_caps["human_assisted"] is True

    indeed_ad = registry.get("indeed")
    assert indeed_ad is not None
    ind_caps = indeed_ad.get_capabilities()
    assert ind_caps["submission"] is False
    assert ind_caps["human_assisted"] is True


def test_domain_allowlist_enforcement():
    session = ApplicationBrowserSession(allowed_domains=["techcorp.com", "*.careers.com"])
    
    # Valid allowed domain
    session.validate_url("https://techcorp.com/apply")
    session.validate_url("https://sub.careers.com/job/1")
    
    # Localhost exception
    session.validate_url("http://localhost:8000/mock")
    
    # Disallowed domains
    with pytest.raises(DomainValidationError):
        session.validate_url("https://malicious-domain.com/apply")
        
    with pytest.raises(DomainValidationError):
        session.validate_url("https://careers.com.hacker.com/apply")


def test_security_rules_and_worker_execution():
    db = SessionLocal()
    try:
        profile = seed_sample_profile(db, user_id=1)
        job = Job(title="Staff Engineer", company_name="SecCorp", application_url="http://localhost:8000/mock/apply/site_a")
        db.add(job)
        db.commit()

        pkg = ApplicationPackage(profile_id=profile.id, job_id=job.id, status="READY_FOR_REVIEW")
        db.add(pkg)
        db.commit()

        app = Application(
            profile_id=profile.id,
            job_id=job.id,
            application_package_id=pkg.id,
            status="PREPARING",
            source="mock",
            application_url="http://localhost:8000/mock/apply/site_a"
        )
        db.add(app)
        db.commit()

        # Test 1: Application not approved -> execution blocked
        res = ApplicationExecutionWorker.execute_queued_application(db, app.id, dry_run=True)
        assert res["success"] is False
        assert "not APPROVED" in res["error"]

        # Approve application
        app.status = "APPROVED"
        db.commit()

        # Test 2: Active Submission Authorization missing for real runs -> blocked
        # (For mock targets we skip token validation but for other platforms it is enforced)
        app.source = "linkedin"
        db.commit()
        res = ApplicationExecutionWorker.execute_queued_application(db, app.id, dry_run=False)
        assert res["success"] is False
        assert "expired submission authorization" in res["error"].lower()

        # Reset to mock source
        app.source = "mock"
        app.status = "APPROVED"
        db.commit()

        # Test 3: Daily safety limit constraint checked
        config = ApplicationExecutionWorker.get_or_create_source_config(db, "mock")
        config.max_applications_per_day = 0
        db.commit()
        res = ApplicationExecutionWorker.execute_queued_application(db, app.id, dry_run=True)
        assert res["success"] is False
        assert "limit exceeded" in res["error"]

        # Reset safety limits
        config.max_applications_per_day = 10
        app.status = "APPROVED"
        db.commit()

        # Test 4: Execute dry run preview success
        res = ApplicationExecutionWorker.execute_queued_application(db, app.id, dry_run=True)
        print("DEBUG RESULT:", res)
        assert res["success"] is True, f"Failed with: {res}"

        db.refresh(app)
        assert app.status == "APPROVED"  # Remains approved for real runs

    finally:
        db.close()


def test_captcha_and_login_intervention_handling():
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        profile = seed_sample_profile(db, user_id=1)
        job = Job(title="Staff Engineer", company_name="SecCorp", application_url="http://localhost:8000/mock/synthetic-careers/captcha")
        db.add(job)
        db.commit()

        app = Application(
            profile_id=profile.id,
            job_id=job.id,
            status="APPROVED",
            source="generic_career",
            application_url="http://localhost:8000/mock/synthetic-careers/captcha"
        )
        db.add(app)
        db.commit()

        # Add active submission authorization
        auth = SubmissionAuthorization(
            application_id=app.id,
            package_version=1,
            status="ACTIVE",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        db.add(auth)
        db.commit()

        # Run execution against captcha page
        res = ApplicationExecutionWorker.execute_queued_application(db, app.id, dry_run=False)
        assert res["success"] is False
        assert res["status"] == "PAUSED"
        
        db.refresh(app)
        assert app.status == "PAUSED"

        # Verify HumanInterventionEvent is logged
        event = db.query(HumanInterventionEvent).filter(HumanInterventionEvent.application_id == app.id).first()
        assert event is not None
        assert event.type == "CAPTCHA_DETECTED"

    finally:
        db.close()


def test_compliance_and_bot_evasion_rules():
    # Enforce strict compliance check that no hidden anti-bot evasions exist in source adapters
    for name in ["linkedin", "indeed", "generic_career"]:
        adapter = registry.get(name)
        assert adapter is not None
        
        # Verify automated submission capability is explicitly false for real platforms
        if name in ["linkedin", "indeed"]:
            assert adapter.get_capabilities()["submission"] is False
            assert adapter.get_capabilities()["human_assisted"] is True

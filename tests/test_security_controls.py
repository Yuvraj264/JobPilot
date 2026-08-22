import time
import pytest
from app.database.connection import SessionLocal
from app.models.job import Job
from app.models.profile import UserProfile
from app.models.application import Application, SubmissionAuthorization
from app.models.tailoring import ApplicationPackage
from app.services.seed_service import seed_sample_profile
from app.services.application.approval_service import ApplicationApprovalService
from app.services.application.authorization_service import SubmissionAuthorizationService
from app.services.submission.submission_engine import SubmissionEngine


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_security_a_submit_without_approval(db_session):
    """
    Test A (Requirement 32): Call submit without approval -> Blocked.
    """
    profile = seed_sample_profile(db_session, user_id=1)
    job = Job(title="QA Engineer A", company_name="Security Corp A", application_url="http://localhost:8000/mock/apply/1")
    db_session.add(job)
    db_session.commit()

    app = Application(profile_id=profile.id, job_id=job.id, status="PREPARING")
    db_session.add(app)
    db_session.commit()

    with pytest.raises(ValueError, match="SECURITY CONTROL: Application status"):
        SubmissionEngine.execute_submission(db_session, app.id)


def test_security_b_submit_without_authorization(db_session):
    """
    Test B (Requirement 32): Call submit without submission authorization -> Blocked.
    """
    profile = seed_sample_profile(db_session, user_id=1)
    job = Job(title="QA Engineer B", company_name="Security Corp B", application_url="http://localhost:8000/mock/apply/2")
    db_session.add(job)
    db_session.commit()

    pkg = ApplicationPackage(profile_id=profile.id, job_id=job.id, status="READY_FOR_REVIEW")
    db_session.add(pkg)
    db_session.commit()

    app = Application(profile_id=profile.id, job_id=job.id, application_package_id=pkg.id, status="APPROVED")
    db_session.add(app)
    db_session.commit()

    with pytest.raises(ValueError, match="SUBMISSION BLOCKED BY SECURITY CONTROL"):
        SubmissionEngine.execute_submission(db_session, app.id)


def test_security_c_submit_with_expired_authorization(db_session):
    """
    Test C (Requirement 32): Call submit with expired authorization -> Blocked.
    """
    profile = seed_sample_profile(db_session, user_id=1)
    job = Job(title="QA Engineer C", company_name="Security Corp C", application_url="http://localhost:8000/mock/apply/3")
    db_session.add(job)
    db_session.commit()

    pkg = ApplicationPackage(profile_id=profile.id, job_id=job.id, status="READY_FOR_REVIEW")
    db_session.add(pkg)
    db_session.commit()

    app = Application(profile_id=profile.id, job_id=job.id, application_package_id=pkg.id, status="APPROVED")
    db_session.add(app)
    db_session.commit()

    # Authorize with -1 minute duration (expired)
    auth = SubmissionAuthorizationService.authorize_submission(db_session, app.id, duration_minutes=-1)

    with pytest.raises(ValueError, match="EXPIRED"):
        SubmissionEngine.execute_submission(db_session, app.id)


def test_security_d_submit_with_revoked_authorization(db_session):
    """
    Test D (Requirement 32): Call submit with revoked authorization -> Blocked.
    """
    profile = seed_sample_profile(db_session, user_id=1)
    job = Job(title="QA Engineer D", company_name="Security Corp D", application_url="http://localhost:8000/mock/apply/4")
    db_session.add(job)
    db_session.commit()

    pkg = ApplicationPackage(profile_id=profile.id, job_id=job.id, status="READY_FOR_REVIEW")
    db_session.add(pkg)
    db_session.commit()

    app = Application(profile_id=profile.id, job_id=job.id, application_package_id=pkg.id, status="APPROVED")
    db_session.add(app)
    db_session.commit()

    auth = SubmissionAuthorizationService.authorize_submission(db_session, app.id)
    SubmissionAuthorizationService.revoke_authorization(db_session, app.id)

    with pytest.raises(ValueError, match="REVOKED"):
        SubmissionEngine.execute_submission(db_session, app.id)


def test_security_f_duplicate_submission_blocked(db_session):
    """
    Test F (Requirement 32): Call submit twice after successful submission (idempotency) -> Blocked.
    """
    from app.services.automation.execution_worker import ApplicationExecutionWorker
    config = ApplicationExecutionWorker.get_or_create_source_config(db_session, "mock_platform")
    config.enabled = True
    db_session.commit()

    profile = seed_sample_profile(db_session, user_id=1)
    job = Job(title="QA Engineer F", company_name="Security Corp F", application_url="http://localhost:8000/mock/apply/5")
    db_session.add(job)
    db_session.commit()

    pkg = ApplicationPackage(profile_id=profile.id, job_id=job.id, status="READY_FOR_REVIEW")
    db_session.add(pkg)
    db_session.commit()

    app = Application(profile_id=profile.id, job_id=job.id, application_package_id=pkg.id, status="APPROVED")
    db_session.add(app)
    db_session.commit()

    auth = SubmissionAuthorizationService.authorize_submission(db_session, app.id)
    res = SubmissionEngine.execute_submission(db_session, app.id)
    assert res["success"] is True

    with pytest.raises(ValueError, match="IDEMPOTENCY CONSTRAINT"):
        SubmissionEngine.execute_submission(db_session, app.id)


def test_ssrf_protection_service():
    from app.services.url_security_service import URLSecurityService
    from app.config import settings

    # Test allowed public domain
    assert URLSecurityService.validate_url("https://greenhouse.io", ["greenhouse.io"]) is True

    # Test domain not in allowlist
    with pytest.raises(ValueError, match="not allowed"):
        URLSecurityService.validate_url("https://google.com", ["greenhouse.io"])

    # Temporarily disable dev local allowance to test production-style checks
    orig_allow = settings.ALLOW_LOCAL_URLS_FOR_DEV
    settings.ALLOW_LOCAL_URLS_FOR_DEV = False
    try:
        # Test loopback IP block
        with pytest.raises(ValueError, match="loopback IP"):
            URLSecurityService.validate_url("http://127.0.0.1")

        # Test private IP blocks
        with pytest.raises(ValueError, match="private network IP"):
            URLSecurityService.validate_url("http://192.168.1.50")

        # Test metadata IP block
        with pytest.raises(ValueError, match="metadata endpoint"):
            URLSecurityService.validate_url("http://169.254.169.254")
    finally:
        settings.ALLOW_LOCAL_URLS_FOR_DEV = orig_allow


def test_api_rate_limiting_middleware():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.config import settings

    client = TestClient(app)
    orig_limit = settings.API_RATE_LIMIT_PER_MINUTE
    # Set limit to 2 for quick testing
    settings.API_RATE_LIMIT_PER_MINUTE = 2
    try:
        # First request
        res1 = client.get("/api/applications", headers={"X-User-Id": "1", "X-Test-Rate-Limit": "true"})
        assert res1.status_code != 429

        # Second request
        res2 = client.get("/api/applications", headers={"X-User-Id": "1", "X-Test-Rate-Limit": "true"})
        assert res2.status_code != 429

        # Third request (exceeds limit of 2)
        res3 = client.get("/api/applications", headers={"X-User-Id": "1", "X-Test-Rate-Limit": "true"})
        assert res3.status_code == 429
        assert res3.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
    finally:
        settings.API_RATE_LIMIT_PER_MINUTE = orig_limit


def test_idor_api_authorization_controls(db_session):
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Pre-create users in DB if they do not exist
    from app.models.profile import User
    u1 = db_session.query(User).filter(User.id == 999100).first()
    if not u1:
        u1 = User(id=999100, email="user999100@example.com")
        db_session.add(u1)
    
    u2 = db_session.query(User).filter(User.id == 999200).first()
    if not u2:
        u2 = User(id=999200, email="user999200@example.com")
        db_session.add(u2)
        
    db_session.commit()

    # 1. Create a resume for User 999100
    res_upload = client.post(
        "/api/resumes",
        data={"name": "User 1 Resume"},
        files={"file": ("resume.pdf", b"%PDF-1.4...", "application/pdf")},
        headers={"X-User-Id": "999100"}
    )
    assert res_upload.status_code == 201
    resume_id = res_upload.json()["id"]

    # 2. Access the resume as User 999100 -> Success
    get_res1 = client.get(f"/api/resumes/{resume_id}", headers={"X-User-Id": "999100"})
    assert get_res1.status_code == 200

    # 3. Access the resume as User 999200 -> 404 Not Found (IDOR protected)
    get_res2 = client.get(f"/api/resumes/{resume_id}", headers={"X-User-Id": "999200"})
    assert get_res2.status_code == 404


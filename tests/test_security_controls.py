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

    with pytest.raises(ValueError, match="SUBMISSION BLOCKED BY SECURITY CONTROL"):
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

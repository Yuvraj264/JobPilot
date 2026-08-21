import time
import pytest
from app.database.connection import SessionLocal
from app.models.job import Job
from app.models.tailoring import ApplicationPackage
from app.models.application import Application
from app.services.seed_service import seed_sample_profile
from app.services.application.approval_service import ApplicationApprovalService
from app.services.application.authorization_service import SubmissionAuthorizationService
from app.services.submission.submission_engine import SubmissionEngine
from app.services.application.audit_service import ApplicationAuditService


def test_application_e2e_full_submission_flow():
    """
    End-to-End Application Control Flow (Requirement 37):
    Job -> Package -> Application -> Validate -> READY_FOR_REVIEW -> Human Approval -> Submission Authorization -> Mock Submission -> Verification -> SUBMITTED -> Audit Timeline
    """
    db = SessionLocal()
    try:
        profile = seed_sample_profile(db, user_id=1)

        job = Job(id=301, title="Senior Automation Engineer", company_name="Mock Corp", application_url="http://localhost:8000/mock/apply/301")
        db.add(job)
        db.commit()

        pkg = ApplicationPackage(id=301, profile_id=profile.id, job_id=job.id, status="READY_FOR_REVIEW")
        db.add(pkg)
        db.commit()

        # 1. Create Application
        app = Application(
            profile_id=profile.id,
            job_id=job.id,
            application_package_id=pkg.id,
            status="PREPARING"
        )
        db.add(app)
        db.commit()

        # 2. Request Review
        app = ApplicationApprovalService.request_review(db, app.id)
        assert app.status == "READY_FOR_REVIEW"

        # 3. Human Approval (with explicit confirmation)
        app = ApplicationApprovalService.approve_application(db, app.id, user_confirmed=True, notes="Explicit human approval granted.")
        assert app.status == "APPROVED"

        # 4. Issue Submission Authorization
        auth = SubmissionAuthorizationService.authorize_submission(db, app.id)
        assert auth.status == "ACTIVE"
        assert app.status == "SUBMISSION_AUTHORIZED"

        # 5. Execute Mock Submission Engine
        res = SubmissionEngine.execute_submission(db, app.id)
        assert res["success"] is True
        assert res["status"] == "SUBMITTED"
        assert res["submission_id"].startswith("SUB-")

        # 6. Verify Final Application Status & Audit Timeline
        db.refresh(app)
        assert app.status == "SUBMITTED"
        assert app.submitted_at is not None

        timeline = ApplicationAuditService.get_timeline(db, app.id)
        assert len(timeline) >= 4
        event_types = [e["event_type"] for e in timeline]
        assert "REVIEW_REQUESTED" in event_types
        assert "APPLICATION_APPROVED" in event_types
        assert "SUBMISSION_AUTHORIZED" in event_types
        assert "APPLICATION_SUBMITTED" in event_types

    finally:
        db.close()

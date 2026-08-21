from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.application import (
    Application,
    SubmissionAuthorization,
    SubmissionRun,
)
from app.services.application.authorization_service import SubmissionAuthorizationService
from app.services.application.snapshot_service import ApplicationSnapshotService
from app.services.application.audit_service import ApplicationAuditService
from app.services.submission.mock_adapter import MockSubmissionAdapter


class SubmissionEngine:
    """
    Submission Engine enforcing mandatory server-side security checks, idempotency rules,
    retry policies, and submission execution logging.
    """

    @staticmethod
    def execute_submission(
        db: Session,
        application_id: int,
        trigger_mock_captcha: bool = False
    ) -> Dict[str, Any]:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        # 1. IDEMPOTENCY CHECK: Prevent duplicate submission if already submitted
        if app.status == "SUBMITTED":
            raise ValueError("IDEMPOTENCY CONSTRAINT: Application has already been SUBMITTED. Duplicate submission blocked.")

        # 2. SERVER-SIDE SECURITY CHECK: Validate Submission Authorization
        auth_val = SubmissionAuthorizationService.validate_authorization(db, application_id)
        if not auth_val["valid"]:
            raise ValueError(f"SUBMISSION BLOCKED BY SECURITY CONTROL: {auth_val['reason']}")

        auth: SubmissionAuthorization = auth_val["authorization"]

        # 3. Create Submission Run DB Record
        sub_run = SubmissionRun(
            application_id=app.id,
            authorization_id=auth.id,
            adapter="MOCK_SUBMISSION",
            started_at=datetime.now(),
            state="NOT_STARTED",
            status="RUNNING"
        )
        db.add(sub_run)
        app.status = "SUBMITTING"
        db.commit()

        ApplicationAuditService.log_event(db, app.id, "SUBMISSION_STARTED", "SYSTEM", {"run_id": sub_run.id})

        # 4. Instantiate Mock Submission Adapter
        adapter = MockSubmissionAdapter()

        app_payload = {
            "application_id": app.id,
            "job_title": app.job.title if app.job else "Target Role",
            "company_name": app.job.company_name if app.job else "Target Company",
            "job_url": app.job.job_url or app.job.application_url if app.job else "",
            "trigger_mock_captcha": trigger_mock_captcha
        }

        # 5. Prepare Submission
        prep_res = adapter.prepare(app_payload)
        if prep_res.get("paused"):
            sub_run.state = "PAUSED"
            sub_run.status = "PAUSED"
            sub_run.error_message = prep_res.get("reason")
            app.status = "PAUSED"
            db.commit()
            ApplicationAuditService.log_event(db, app.id, "SUBMISSION_PAUSED", "SYSTEM", {"reason": prep_res.get("reason")})
            return {
                "success": False,
                "status": "PAUSED",
                "reason": prep_res.get("reason"),
                "sub_run_id": sub_run.id
            }

        # 6. Execute Submission
        sub_res = adapter.submit(app_payload)

        # 7. Verify Submission Success
        verified = adapter.verify_submission(sub_res)
        if not verified:
            sub_run.state = "FAILED"
            sub_run.status = "FAILED"
            sub_run.error_message = "Submission verification failed."
            app.status = "FAILED"
            db.commit()
            ApplicationAuditService.log_event(db, app.id, "SUBMISSION_FAILED", "SYSTEM", {"error": sub_run.error_message})
            return {
                "success": False,
                "status": "FAILED",
                "error": sub_run.error_message,
                "sub_run_id": sub_run.id
            }

        # 8. Success: Capture Snapshot, Update Authorization to USED, Update Application Status to SUBMITTED
        ApplicationSnapshotService.create_snapshot(db, app.id)

        auth.status = "USED"
        sub_run.state = "SUBMITTED"
        sub_run.status = "COMPLETED"
        sub_run.completed_at = datetime.now()
        sub_run.submission_id = sub_res["submission_id"]
        sub_run.confirmation = sub_res["confirmation"]

        app.status = "SUBMITTED"
        app.submitted_at = datetime.now()
        db.commit()

        ApplicationAuditService.log_event(db, app.id, "SUBMISSION_VERIFIED", "SYSTEM", {
            "submission_id": sub_res["submission_id"],
            "confirmation": sub_res["confirmation"]
        })
        ApplicationAuditService.log_event(db, app.id, "APPLICATION_SUBMITTED", "SYSTEM", {
            "status": "SUBMITTED"
        })

        return {
            "success": True,
            "status": "SUBMITTED",
            "submission_id": sub_res["submission_id"],
            "confirmation": sub_res["confirmation"],
            "sub_run_id": sub_run.id
        }

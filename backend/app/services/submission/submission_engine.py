from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.application import (
    Application,
    SubmissionAuthorization,
    SubmissionRun,
)
from app.config import settings
from app.services.application.validation_service import ApplicationValidationService
from app.services.application.authorization_service import SubmissionAuthorizationService
from app.services.application.snapshot_service import ApplicationSnapshotService
from app.services.application.audit_service import ApplicationAuditService
from app.services.submission.mock_adapter import MockSubmissionAdapter


class SubmissionEngine:
    """
    Submission Engine enforcing 14 backend validation checks, transaction locking,
    race condition protections, idempotency rules, and submission execution logging.
    """

    @classmethod
    def execute_submission(
        cls,
        db: Session,
        application_id: int,
        trigger_mock_captcha: bool = False
    ) -> Dict[str, Any]:
        # 1. Concurrency Control: Select application with database row-level locking (FOR UPDATE)
        app = db.query(Application).filter(Application.id == application_id).with_for_update().first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        profile_id = app.profile_id
        profile = app.profile

        # 2. Idempotency Check: Prevent duplicate submission if already submitted
        if app.status == "SUBMITTED":
            raise ValueError("IDEMPOTENCY CONSTRAINT: Application has already been SUBMITTED. Duplicate submission blocked.")

        # 3. Race Condition Check: Block if another worker is already processing
        if app.status == "SUBMITTING":
            raise ValueError("CONCURRENCY CONTROL: Application submission is already in progress.")

        # 4. Check profile association ownership
        if not profile or app.profile_id != profile.id:
            raise ValueError("SECURITY CONTROL: Profile owner mismatch.")

        # 5. Check if application is approved
        if app.status not in ["APPROVED", "SUBMISSION_AUTHORIZED"]:
            raise ValueError(f"SECURITY CONTROL: Application status is '{app.status}', expected APPROVED or SUBMISSION_AUTHORIZED.")

        # 6 & 7 & 8 & 9 & 10. Validate submission authorization (exists, active, unexpired, unrevoked, exact package version)
        auth_val = SubmissionAuthorizationService.validate_authorization(db, application_id)
        if not auth_val["valid"]:
            raise ValueError(f"SUBMISSION BLOCKED BY SECURITY CONTROL: {auth_val['reason']}")

        auth: SubmissionAuthorization = auth_val["authorization"]

        # 11. Check if job is still valid (ACTIVE or DISCOVERED status)
        if not app.job or app.job.status not in ["ACTIVE", "DISCOVERED"]:
            raise ValueError("SECURITY CONTROL: Target job listing is no longer active or valid.")

        # 12. Check if daily application safety limit is exceeded
        today = datetime.now().date()
        today_start = datetime(today.year, today.month, today.day)
        submitted_today = db.query(Application).filter(
            Application.profile_id == profile_id,
            Application.status == "SUBMITTED",
            Application.submitted_at >= today_start
        ).count()
        if submitted_today >= settings.MAX_APPLICATIONS_PER_DAY:
            raise ValueError(f"LIMIT ENFORCEMENT: Daily applications submission limit ({settings.MAX_APPLICATIONS_PER_DAY}) exceeded.")

        # 13 & 14. Check source capability and mode compatibility
        from app.services.automation.execution_worker import ApplicationExecutionWorker
        config = ApplicationExecutionWorker.get_or_create_source_config(db, app.source)
        if config:
            if not config.enabled:
                raise ValueError("SECURITY CONTROL: Application source target is currently disabled.")
            if config.mode == "UNSUPPORTED":
                raise ValueError("SECURITY CONTROL: Platform source has unsupported automation capability.")

        # 15. Check that no blocking validation errors exist
        val = ApplicationValidationService.validate_application(
            db, app.job, app.profile, app.selected_resume, app.tailored_resume, app.package
        )
        if not val["valid"]:
            raise ValueError(f"VALIDATION CONSTRAINT: Blocking validation issues exist: {', '.join(val['blocking_issues'])}")

        # Atomically transition to SUBMITTING state immediately to lock operations
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

        # 16. Instantiate Mock Submission Adapter
        adapter = MockSubmissionAdapter()

        app_payload = {
            "application_id": app.id,
            "job_title": app.job.title if app.job else "Target Role",
            "company_name": app.job.company_name if app.job else "Target Company",
            "job_url": app.job.job_url or app.job.application_url if app.job else "",
            "trigger_mock_captcha": trigger_mock_captcha
        }

        # 17. Prepare Submission
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

        # 18. Execute Submission
        sub_res = adapter.submit(app_payload)

        # 19. Verify Submission Success
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

        # 20. Success: Capture Snapshot, Update Authorization to USED, Update Application Status to SUBMITTED
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

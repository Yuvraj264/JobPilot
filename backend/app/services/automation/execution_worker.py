from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
import logging
from sqlalchemy.orm import Session

from app.models.application import (
    Application,
    ApplicationQueue,
    ApplicationSourceConfiguration,
    HumanInterventionEvent,
    SubmissionAuthorization,
    SubmissionRun,
    ApplicationSnapshot
)
from app.models.job import JobSource
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.services.automation.browser_session import ApplicationBrowserSession, DomainValidationError
from app.services.automation.adapters.registry import registry
from app.services.automation.action_planner import ApplicationActionPlanner
from app.services.automation.action_executor import ApplicationActionExecutor
from app.services.application.snapshot_service import ApplicationSnapshotService
from app.services.application.audit_service import ApplicationAuditService

logger = logging.getLogger(__name__)


class ApplicationExecutionWorker:
    """
    Worker class responsible for executing queued applications.
    Handles dry-run modes, approval and token verification, field mapping, redirects,
    intervention events, and safety limits.
    """

    @staticmethod
    def get_or_create_source_config(db: Session, source_name: str) -> ApplicationSourceConfiguration:
        # Resolve source name to DB JobSource record
        source = db.query(JobSource).filter(JobSource.name == source_name.lower()).first()
        if not source:
            source = JobSource(
                name=source_name.lower(),
                display_name=source_name.capitalize(),
                enabled=True,
                source_type="API" if source_name in ["greenhouse", "lever"] else "CRAWLER"
            )
            db.add(source)
            db.commit()
            db.refresh(source)

        config = db.query(ApplicationSourceConfiguration).filter(
            ApplicationSourceConfiguration.source_id == source.id
        ).first()

        if not config:
            # Safe default configuration parameters
            config = ApplicationSourceConfiguration(
                source_id=source.id,
                enabled=True if source_name.lower() in ["mock", "generic_career"] else False,
                mode="HUMAN_ASSISTED",
                allowed_domains=["localhost", "127.0.0.1"],
                capabilities={
                    "form_filling": True,
                    "resume_upload": True,
                    "submission": False,
                    "human_assisted": True
                },
                max_applications_per_run=5,
                max_applications_per_day=10,
                max_failed_attempts=3,
                max_human_interventions=5,
                require_human_review=True
            )
            db.add(config)
            db.commit()
            db.refresh(config)

        return config

    @classmethod
    def execute_queued_application(
        cls,
        db: Session,
        application_id: int,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        
        # 1. Retrieve Application
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return {"success": False, "error": f"Application {application_id} not found."}

        # 2. Duplicate Check
        if app.status == "SUBMITTED":
            return {"success": False, "error": "Application is already SUBMITTED. Duplicate blocked."}

        # 3. Verify Approval
        if app.status not in ["APPROVED", "SUBMISSION_AUTHORIZED", "SUBMITTING"]:
            app.status = "FAILED"
            db.commit()
            ApplicationAuditService.log_event(db, app.id, "EXECUTION_FAILED", "SYSTEM", {"error": "Application is not APPROVED."})
            return {"success": False, "error": f"Application {application_id} has status '{app.status}' and is not APPROVED."}

        # 4. Verify Authorization
        # Skip token check only for dry-runs or mock portals
        if not dry_run and app.source != "MOCK_PLATFORM":
            active_auth = db.query(SubmissionAuthorization).filter(
                SubmissionAuthorization.application_id == app.id,
                SubmissionAuthorization.status == "ACTIVE"
            ).first()
            if not active_auth or active_auth.expires_at < datetime.now():
                app.status = "FAILED"
                db.commit()
                ApplicationAuditService.log_event(db, app.id, "EXECUTION_FAILED", "SYSTEM", {"error": "Invalid or expired submission authorization."})
                return {"success": False, "error": "Invalid/Expired submission authorization token."}

        # Update queue state
        queue_rec = db.query(ApplicationQueue).filter(ApplicationQueue.application_id == app.id).first()
        if queue_rec:
            queue_rec.status = "RUNNING"
            queue_rec.started_at = datetime.now()
            db.commit()

        # 5. Resolve Source Config
        source_name = app.source.lower() if app.source else "mock"
        config = cls.get_or_create_source_config(db, source_name)

        # Safety Check: Configuration limits check
        # Enforce enabled flag
        if not config.enabled and source_name != "mock":
            if queue_rec:
                queue_rec.status = "FAILED"
            app.status = "FAILED"
            db.commit()
            return {"success": False, "error": f"Application source '{app.source}' is disabled in configuration."}

        # Safety Check: Daily applications limits check
        today_runs_count = db.query(SubmissionRun).filter(
            SubmissionRun.started_at >= datetime.now() - timedelta(days=1),
            SubmissionRun.status == "COMPLETED"
        ).count()
        if today_runs_count >= config.max_applications_per_day:
            if queue_rec:
                queue_rec.status = "FAILED"
            app.status = "FAILED"
            db.commit()
            ApplicationAuditService.log_event(db, app.id, "LIMIT_EXCEEDED", "SYSTEM", {"limit": "max_applications_per_day"})
            return {"success": False, "error": "Daily applications limit exceeded."}

        # 6. Resolve Adapter
        adapter = registry.get(source_name)
        if not adapter:
            # Fallback to Generic Career Adapter if domain matches generic career sites
            adapter = registry.get("generic_career")
            if not adapter:
                return {"success": False, "error": f"No adapter registered for source '{app.source}'."}

        # 7. Start Session
        # Default safety: DRY_RUN = true
        # Allowed domains allowlist validation
        allowed_domains = config.allowed_domains or ["localhost", "127.0.0.1"]
        session = ApplicationBrowserSession(allowed_domains=allowed_domains, headless=True)

        # 8. Create Submission Run DB Record
        sub_run = SubmissionRun(
            application_id=app.id,
            adapter=adapter.name(),
            started_at=datetime.now(),
            state="NOT_STARTED",
            status="RUNNING"
        )
        db.add(sub_run)
        db.commit()

        # Create/find AutomationRun matching standard mapping
        from app.models.automation import AutomationRun
        auto_run = AutomationRun(
            profile_id=app.profile_id,
            job_id=app.job_id,
            started_at=datetime.now(timezone.utc),
            state="CREATED",
            status="RUNNING",
            current_url=app.application_url or app.job.application_url
        )
        db.add(auto_run)
        db.commit()

        ApplicationAuditService.log_event(db, app.id, "SUBMISSION_STARTED", "SYSTEM", {"run_id": sub_run.id, "adapter": adapter.name(), "dry_run": dry_run})

        try:
            session.start()
            
            # Step 9 & 10: Navigate and check redirects/allowed domain allowlist
            app_url = app.application_url or app.job.application_url or app.job.job_url
            if not app_url:
                raise ValueError("Target application URL is empty.")

            logger.info(f"Worker navigating browser session to: {app_url}")
            session.navigate(app_url)
            sub_run.state = "PREPARING"
            auto_run.state = "OPENING"
            db.commit()

            # Captcha and Login Intervention Check
            intervention = adapter.detect_intervention(session)
            if intervention.get("required"):
                cls._handle_intervention(db, app, queue_rec, sub_run, auto_run, session, intervention.get("type"), intervention.get("reason"))
                return {"success": False, "status": "PAUSED", "reason": intervention.get("reason")}

            # 11. Run Inspection and Preparation
            auto_run.state = "INSPECTING"
            db.commit()
            inspection = adapter.inspect(session)

            # Check if visual inspector found any CAPTCHA or logins
            if inspection.get("has_captcha"):
                cls._handle_intervention(db, app, queue_rec, sub_run, auto_run, session, "CAPTCHA_DETECTED", "CAPTCHA element detected in HTML DOM.")
                return {"success": False, "status": "PAUSED", "reason": "CAPTCHA challenge detected."}

            auto_run.state = "PLANNING"
            db.commit()
            
            # Form field mapping planning
            default_resume = db.query(Resume).filter(Resume.id == app.selected_resume_id).first()
            if not default_resume:
                default_resume = db.query(Resume).filter(Resume.profile_id == app.profile_id).first()

            plan = ApplicationActionPlanner.plan_page_actions(
                inspection, app.profile, default_resume, db=db, automation_run_id=auto_run.id, job_id=app.job_id
            )

            # Record action logs preview
            actions = plan.get("actions", [])
            for act in actions:
                logger.info(f"Planned action: {act.get('action')} -> {act.get('field_type')}")

            if not plan.get("automatable"):
                # Missing required fields or low mapping confidence
                cls._handle_intervention(
                    db, app, queue_rec, sub_run, auto_run, session, 
                    "AMBIGUOUS_FIELD", plan.get("pause_reason", "Fields mapping failed.")
                )
                return {"success": False, "status": "PAUSED", "reason": plan.get("pause_reason")}

            # Execute Field Mapping actions
            sub_run.state = "FILLING"
            auto_run.state = "FILLING"
            db.commit()

            # 12. Dry Run Mode Logic
            if dry_run:
                # Capture screenshots but do not submit
                shot = session.capture_screenshot(f"dryrun_{app.id}")
                sub_run.state = "READY"
                sub_run.status = "COMPLETED"
                sub_run.completed_at = datetime.now()
                sub_run.confirmation = "DRY_RUN_PREVIEW_VERIFIED"
                
                auto_run.state = "READY_FOR_REVIEW"
                auto_run.status = "COMPLETED"
                auto_run.completed_at = datetime.now(timezone.utc)
                if shot:
                    auto_run.screenshots = [shot]

                app.status = "APPROVED"  # Keep in approved state
                if queue_rec:
                    queue_rec.status = "COMPLETED"
                    queue_rec.completed_at = datetime.now()
                db.commit()

                ApplicationAuditService.log_event(db, app.id, "SUBMISSION_PREVIEW_SUCCESS", "SYSTEM", {"dry_run": True})
                session.stop()
                return {"success": True, "status": "DRY_RUN_SUCCESS", "actions_planned": len(actions)}

            # 13. Real Execution Mode
            # Verify approval checks before submission execution
            if config.mode == "MANUAL" or not config.capabilities.get("submission", False):
                cls._handle_intervention(
                    db, app, queue_rec, sub_run, auto_run, session,
                    "UNSUPPORTED_FIELD", "Platform does not permit automated submissions. Please complete submission manually."
                )
                return {"success": False, "status": "PAUSED", "reason": "Automated submission restricted."}

            # Execute fields autofill
            for act in actions:
                res = ApplicationActionExecutor.execute_action(db, auto_run.id, session.controller, act)
                if res.get("status") == "SUCCESS":
                    auto_run.actions_completed += 1
                else:
                    auto_run.actions_failed += 1
                    cls._handle_intervention(db, app, queue_rec, sub_run, auto_run, session, "UNSUPPORTED_FIELD", res.get("reason", "Field fill action failed."))
                    return {"success": False, "status": "PAUSED", "reason": "Action executor failed to fill form."}

            # Verify action outputs
            auto_run.state = "VERIFYING"
            sub_run.state = "VERIFYING"
            db.commit()

            # Execute submission
            sub_res = adapter.submit(session)
            if not sub_res.get("success"):
                cls._handle_intervention(
                    db, app, queue_rec, sub_run, auto_run, session, 
                    "SUBMISSION_UNVERIFIED", sub_res.get("error", "Verification failure.")
                )
                return {"success": False, "status": "PAUSED", "reason": "Submission verification failed."}

            # Verify Success
            verified = adapter.verify_submission(session, sub_res)
            if not verified:
                cls._handle_intervention(
                    db, app, queue_rec, sub_run, auto_run, session,
                    "SUBMISSION_UNVERIFIED", "Confirmation page or success text could not be verified."
                )
                return {"success": False, "status": "PAUSED", "reason": "Success verification failed."}

            # Ingest success details
            ApplicationSnapshotService.create_snapshot(db, app.id)

            sub_run.state = "SUBMITTED"
            sub_run.status = "COMPLETED"
            sub_run.completed_at = datetime.now()
            sub_run.submission_id = sub_res.get("submission_id") or f"SUB-{app.id}-{datetime.now().strftime('%m%d%H%M')}"
            sub_run.confirmation = sub_res.get("confirmation") or "Generic Success Confirmation"

            auto_run.state = "SUBMITTED"
            auto_run.status = "COMPLETED"
            auto_run.completed_at = datetime.now(timezone.utc)

            app.status = "SUBMITTED"
            app.submitted_at = datetime.now()

            if queue_rec:
                queue_rec.status = "COMPLETED"
                queue_rec.completed_at = datetime.now()
            db.commit()

            ApplicationAuditService.log_event(db, app.id, "SUBMISSION_VERIFIED", "SYSTEM", {"submission_id": sub_run.submission_id})
            ApplicationAuditService.log_event(db, app.id, "APPLICATION_SUBMITTED", "SYSTEM", {"status": "SUBMITTED"})

            session.stop()
            return {"success": True, "status": "SUBMITTED", "submission_id": sub_run.submission_id}

        except DomainValidationError as dve:
            cls._handle_intervention(db, app, queue_rec, sub_run, auto_run, session, "DOMAIN_CHANGE", str(dve))
            return {"success": False, "status": "PAUSED", "reason": str(dve)}

        except Exception as e:
            logger.error(f"Worker runtime execution error: {e}", exc_info=True)
            db.rollback()
            sub_run.state = "FAILED"
            sub_run.status = "FAILED"
            sub_run.error_message = str(e)
            sub_run.completed_at = datetime.now()

            auto_run.state = "FAILED"
            auto_run.status = "FAILED"
            auto_run.completed_at = datetime.now(timezone.utc)
            auto_run.error_message = str(e)

            app.status = "FAILED"
            if queue_rec:
                queue_rec.status = "FAILED"
                queue_rec.completed_at = datetime.now()
            db.commit()

            ApplicationAuditService.log_event(db, app.id, "EXECUTION_FAILED", "SYSTEM", {"error": str(e)})
            try: session.stop()
            except Exception: pass
            return {"success": False, "error": str(e)}

    @staticmethod
    def _handle_intervention(
        db: Session,
        app: Application,
        queue_rec: Optional[ApplicationQueue],
        sub_run: SubmissionRun,
        auto_run: Any,
        session: ApplicationBrowserSession,
        event_type: str,
        reason: str
    ):
        # Transition state to PAUSED and log HumanInterventionEvent
        sub_run.state = "PAUSED"
        sub_run.status = "PAUSED"
        sub_run.error_message = reason

        auto_run.state = "PAUSED"
        auto_run.status = "PAUSED"
        auto_run.human_intervention_required = True
        auto_run.pause_reason = reason

        shot = ""
        try:
            shot = session.capture_screenshot(f"pause_{app.id}_{event_type.lower()}")
            if shot:
                auto_run.screenshots = (auto_run.screenshots or []) + [shot]
        except Exception:
            pass

        app.status = "PAUSED"
        if queue_rec:
            queue_rec.status = "PAUSED"
        db.commit()

        # Insert intervention event log
        event = HumanInterventionEvent(
            application_id=app.id,
            automation_run_id=auto_run.id,
            type=event_type,
            reason=reason,
            created_at=datetime.now()
        )
        db.add(event)
        db.commit()

        ApplicationAuditService.log_event(db, app.id, "SUBMISSION_PAUSED", "SYSTEM", {"reason": reason, "type": event_type, "screenshot": shot})

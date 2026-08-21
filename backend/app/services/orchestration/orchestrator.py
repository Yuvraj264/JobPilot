from datetime import datetime, timezone
import logging
import threading
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.job import Job, JobSource
from app.models.matching import JobMatch
from app.models.application import Application, ApplicationQueue, SubmissionAuthorization
from app.models.orchestration import OrchestrationRun, AutomationConfiguration
from app.services.job_discovery_service import JobDiscoveryService
from app.services.job_matching_service import JobMatchingService
from app.services.orchestration.selection_service import JobSelectionService
from app.services.tailoring.resume_tailoring_service import ResumeTailoringService
from app.services.tailoring.package_service import ApplicationPackageService
from app.services.application.validation_service import ApplicationValidationService
from app.services.application.approval_service import ApplicationApprovalService
from app.services.application.authorization_service import SubmissionAuthorizationService
from app.services.automation.execution_worker import ApplicationExecutionWorker
from app.services.orchestration.retry_manager import RetryManager
from app.services.orchestration.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class JobPilotOrchestrator:
    """
    Core end-to-end Orchestrator for JobPilot.
    Coordinates Discovery, Matching, Selection, Tailoring, Package, Validation,
    human-review transitions, queues, worker execution, retries, and analytics updates.
    """

    # Thread-safe running state lock
    _run_lock = threading.Lock()
    active_runs: Dict[int, int] = {}  # profile_id -> orchestration_run_id

    @classmethod
    def get_or_create_config(cls, db: Session, profile_id: int) -> AutomationConfiguration:
        """
        Retrieves or creates conservative defaults for profile.
        """
        config = db.query(AutomationConfiguration).filter(
            AutomationConfiguration.profile_id == profile_id
        ).first()

        if not config:
            config = AutomationConfiguration(
                profile_id=profile_id,
                preset_name="CONSERVATIVE",
                is_active=True,
                discovery_enabled=True,
                discovery_sources=["mock", "generic_career"],
                max_jobs_per_run=10,
                minimum_match_score=80.0,
                allowed_recommendations=["APPLY"],
                auto_tailor_resume=True,
                auto_generate_answers=True,
                require_human_review=True,
                auto_approve=False,  # Human review required
                allowed_modes=["HUMAN_ASSISTED"],
                max_applications_per_run=3,
                max_applications_per_day=10,
                dry_run=True,  # Safety dry-run enabled by default
                max_retries=3,
                cooldown_days=30,
                concurrency_limit=1
            )
            db.add(config)
            db.commit()
            db.refresh(config)

        return config

    @classmethod
    def stop_run(cls, db: Session, run_id: int):
        """Cancels a currently executing orchestration run."""
        run = db.query(OrchestrationRun).filter(OrchestrationRun.id == run_id).first()
        if run and run.status == "RUNNING":
            run.status = "CANCELLED"
            run.completed_at = datetime.now()
            db.commit()
            logger.info(f"Orchestration run {run_id} cancelled by user request.")

    @classmethod
    def run_pipeline(
        cls,
        db: Session,
        profile_id: int,
        trigger_type: str = "MANUAL",
        resume_run_id: Optional[int] = None
    ) -> OrchestrationRun:
        """
        Main runner executing or resuming the sequential stages:
        DISCOVER -> MATCH -> SELECT -> PREPARE -> VALIDATE -> REVIEW -> QUEUE -> EXECUTE -> TRACK -> ANALYZE
        """
        with cls._run_lock:
            if profile_id in cls.active_runs and not resume_run_id:
                # Deduplicate concurrent runs
                existing_run_id = cls.active_runs[profile_id]
                existing = db.query(OrchestrationRun).filter(OrchestrationRun.id == existing_run_id).first()
                if existing and existing.status == "RUNNING":
                    logger.warning(f"Orchestration run already active for profile {profile_id}. Ignoring request.")
                    return existing

        profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        if not profile:
            raise ValueError(f"UserProfile {profile_id} not found.")

        config = cls.get_or_create_config(db, profile_id)

        # 1. Initialize or Resume run record
        if resume_run_id:
            run = db.query(OrchestrationRun).filter(OrchestrationRun.id == resume_run_id).first()
            if not run:
                raise ValueError(f"Cannot resume run: OrchestrationRun {resume_run_id} not found.")
            run.status = "RUNNING"
            run.started_at = datetime.now()
            db.commit()
        else:
            run = OrchestrationRun(
                profile_id=profile_id,
                status="RUNNING",
                trigger_type=trigger_type,
                configuration_version=config.preset_name
            )
            db.add(run)
            db.commit()
            db.refresh(run)

        cls.active_runs[profile_id] = run.id

        try:
            # Stage: DISCOVER
            if run.jobs_discovered == 0:
                logger.info("Stage: DISCOVERING jobs.")
                try:
                    discovery_results = JobDiscoveryService.run_discovery_all_enabled(db, limit_per_source=config.max_jobs_per_run)
                    discovered_count = sum(r.get("jobs_discovered", 0) for r in discovery_results if r.get("status") != "FAILED")
                    run.jobs_discovered = discovered_count
                    db.commit()
                except Exception as e:
                    logger.error(f"Error during job discovery: {e}")
                    run.error_count += 1
                    db.commit()

            # Stage: MATCH
            if run.jobs_matched == 0:
                logger.info("Stage: MATCHING jobs.")
                try:
                    match_run = JobMatchingService.run_batch_matching(db, profile_id, limit=50)
                    run.jobs_matched = match_run.jobs_evaluated
                    db.commit()
                except Exception as e:
                    logger.error(f"Error during batch job matching: {e}")
                    run.error_count += 1
                    db.commit()

            # Stage: SELECT
            logger.info("Stage: SELECTING jobs.")
            selected_jobs = JobSelectionService.select_jobs_for_orchestration(db, profile_id, config)
            run.jobs_selected = len(selected_jobs)
            db.commit()

            # Stage: PREPARE & VALIDATE (Failure Isolation enabled per-job loop)
            prepared_apps = []
            for job in selected_jobs:
                # Safety check: Cancel request verification
                db.refresh(run)
                if run.status == "CANCELLED":
                    break

                try:
                    # Ingest or tailor resume
                    tailored = None
                    if config.auto_tailor_resume:
                        logger.info(f"Auto tailoring resume for job {job.id}.")
                        master_res = db.query(Resume).filter(Resume.profile_id == profile_id, Resume.is_default == True).first()
                        tailored = ResumeTailoringService.tailor_resume(db, profile, job, master_resume=master_res)
                        # Simulate auto-validation of tailored resume for mock purposes
                        tailored.status = "VALIDATED"
                        db.commit()

                    # Create package
                    logger.info(f"Assembling ApplicationPackage for job {job.id}.")
                    package = ApplicationPackageService.create_package(
                        db, profile_id, job.id,
                        source_resume_id=master_res.id if 'master_res' in locals() and master_res else None,
                        tailored_resume_id=tailored.id if tailored else None
                    )

                    # Initialize application record
                    app_rec = db.query(Application).filter(
                        Application.application_package_id == package.id
                    ).first()
                    if not app_rec:
                        app_rec = Application(
                            profile_id=profile_id,
                            job_id=job.id,
                            application_package_id=package.id,
                            source=job.source.name if job.source else "mock",
                            application_url=job.application_url or job.job_url,
                            status="PREPARING",
                            selected_resume_id=master_res.id if 'master_res' in locals() and master_res else None,
                            tailored_resume_id=tailored.id if tailored else None
                        )
                        db.add(app_rec)
                        db.commit()
                        db.refresh(app_rec)

                    run.packages_created += 1
                    db.commit()

                    # Validation check
                    val = ApplicationValidationService.validate_application(
                        db, job, profile, master_res if 'master_res' in locals() and master_res else None, tailored, package
                    )
                    if not val["valid"]:
                        logger.warning(f"Validation failed for job {job.id}: {val['blocking_issues']}")
                        app_rec.status = "FAILED"
                        run.applications_failed += 1
                        run.error_count += 1
                        db.commit()
                        continue

                    prepared_apps.append(app_rec)
                    run.applications_ready += 1
                    db.commit()

                except Exception as job_err:
                    logger.error(f"Failed to prepare application for job {job.id}: {job_err}", exc_info=True)
                    run.error_count += 1
                    run.applications_failed += 1
                    db.commit()

            # Stage: REVIEW & APPROVAL & QUEUE
            for app in prepared_apps:
                db.refresh(run)
                if run.status == "CANCELLED":
                    break

                try:
                    if config.require_human_review:
                        if config.auto_approve:
                            # Auto-approve & auto-authorize for conservative automated runs
                            app.status = "APPROVED"
                            db.commit()
                            run.applications_approved += 1

                            # Authorize token
                            auth = SubmissionAuthorization(
                                application_id=app.id,
                                package_version=1,
                                status="ACTIVE",
                                expires_at=datetime.now() + timedelta(hours=config.authorization_expiration_hours)
                            )
                            db.add(auth)
                            
                            # Add to Queue
                            queue_rec = ApplicationQueue(
                                application_id=app.id,
                                priority=match.overall_score if 'match' in locals() and match else 1.0,
                                status="QUEUED"
                            )
                            db.add(queue_rec)
                            db.commit()
                            run.applications_queued += 1
                        else:
                            # Send to user manual review queue
                            app.status = "READY_FOR_REVIEW"
                            db.commit()
                            run.applications_paused += 1
                    else:
                        # Auto queue directly
                        app.status = "APPROVED"
                        db.commit()
                        run.applications_approved += 1

                        queue_rec = ApplicationQueue(
                            application_id=app.id,
                            priority=1.0,
                            status="QUEUED"
                        )
                        db.add(queue_rec)
                        db.commit()
                        run.applications_queued += 1

                except Exception as review_err:
                    logger.error(f"Review stage failed for application {app.id}: {review_err}")
                    run.error_count += 1
                    db.commit()

            # Stage: EXECUTE (Run execution worker logic for queued items)
            # Enforce server-side execution limit constraints
            if not config.dry_run:
                # Live execution checks daily limits
                limit_check = JobSelectionService.check_daily_limits_reached(db, profile_id, config)
                if limit_check["reached"]:
                    logger.warning(f"Live queue execution stopped: {limit_check['reason']}")
                else:
                    queued_items = db.query(ApplicationQueue).filter(ApplicationQueue.status == "QUEUED").all()
                    executed_count = 0
                    for item in queued_items:
                        if executed_count >= config.max_applications_per_run:
                            logger.info(f"Max applications per run limit of {config.max_applications_per_run} reached. Stopping queue worker.")
                            break

                        # Pre-execution safety verification check
                        app_rec = item.application
                        if app_rec.status not in ["APPROVED", "SUBMISSION_AUTHORIZED", "SUBMITTING"]:
                            logger.warning(f"Safety Check: Application {app_rec.id} is in status '{app_rec.status}', skipping execution.")
                            continue

                        # Cooldown check
                        hist = JobSelectionService.get_application_history_status(db, profile_id, app_rec.job, cooldown_days=config.cooldown_days)
                        if hist == "ALREADY_APPLIED":
                            logger.warning(f"Safety Check: Duplicate detected for job {app_rec.job.id}, skipping execution.")
                            continue

                        logger.info(f"Worker executing application {app_rec.id} (dry_run = False).")
                        res = ApplicationExecutionWorker.execute_queued_application(db, app_rec.id, dry_run=False)
                        if res["success"]:
                            run.applications_submitted += 1
                            executed_count += 1
                        else:
                            # If recoverable failure, RetryManager manages limits
                            is_rec = RetryManager.is_recoverable(res.get("error") or res.get("reason", ""))
                            if is_rec and RetryManager.should_retry_application(db, app_rec.id, max_retries=config.max_retries):
                                logger.info(f"Application {app_rec.id} failed with recoverable error. Re-queueing for retry.")
                                item.status = "QUEUED"
                                app_rec.status = "APPROVED"
                            else:
                                run.applications_failed += 1
                            run.error_count += 1
                        db.commit()

            else:
                # Dry run execution preview
                queued_items = db.query(ApplicationQueue).filter(ApplicationQueue.status == "QUEUED").all()
                for item in queued_items:
                    app_rec = item.application
                    logger.info(f"Worker running dry-run preview for application {app_rec.id}.")
                    res = ApplicationExecutionWorker.execute_queued_application(db, app_rec.id, dry_run=True)
                    if res["success"]:
                        run.applications_submitted += 1
                    else:
                        run.applications_failed += 1
                        run.error_count += 1
                    db.commit()

            # Record final run status
            if run.status != "CANCELLED":
                if run.error_count > 0 and run.applications_submitted > 0:
                    run.status = "PARTIAL"
                elif run.error_count > 0:
                    run.status = "FAILED"
                else:
                    run.status = "COMPLETED"

            run.completed_at = datetime.now()
            db.commit()

            # Stage: ANALYZE (Update time-series metrics views)
            AnalyticsService.record_daily_metric(
                db, profile_id,
                discovered=run.jobs_discovered,
                matched=run.jobs_matched,
                prepared=run.packages_created,
                submitted=run.applications_submitted,
                failed=run.applications_failed,
                match_score=85.0
            )

            return run

        except Exception as pipeline_err:
            logger.error(f"Pipeline crashed: {pipeline_err}", exc_info=True)
            db.rollback()
            run.status = "FAILED"
            run.completed_at = datetime.now()
            run.error_count += 1
            db.commit()
            return run
        finally:
            with cls._run_lock:
                cls.active_runs.pop(profile_id, None)

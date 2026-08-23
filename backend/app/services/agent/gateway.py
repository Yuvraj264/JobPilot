import uuid
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.services.agent.policy import AgentPolicyEngine


class AgentActionGateway:
    """
    The exclusive pathway for the Agent to mutate files, database tables, or trigger processes.
    Enforces policy validation and whitelist verification.
    """

    WHITELIST_ACTIONS = [
        "DISCOVER_JOBS",
        "SAVE_JOB",
        "PREPARE_RESUME",
        "GENERATE_ANSWERS",
        "CREATE_PACKAGE",
        "REQUEST_REVIEW",
        "QUEUE_APPLICATION",
        "START_HUMAN_ASSISTED_SESSION",
        "EXECUTE_PERMITTED_APPLICATION",
        "RETRY_OPERATION",
        "STOP_OPERATION"
    ]

    # Simple memory cache for idempotency keys
    _idempotency_cache = set()

    @classmethod
    def execute_action(
        cls,
        db: Session,
        profile_id: int,
        action: str,
        job_id: Optional[int] = None,
        mission_id: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Executes permitted mutations after verifying policy and whitelist checks.
        Returns (success_status, message).
        """
        # 1. Whitelist validation
        if action not in cls.WHITELIST_ACTIONS:
            return False, f"Action Gateway Error: Action '{action}' is not whitelisted."

        # 2. Idempotency control
        if idempotency_key:
            if idempotency_key in cls._idempotency_cache:
                return False, f"Action Gateway Warning: Action skipped due to duplicate idempotency key '{idempotency_key}'."
            cls._idempotency_cache.add(idempotency_key)

        # 3. Policy validation gatekeeper check
        status, reason = AgentPolicyEngine.validate_action(db, profile_id, action, job_id, mission_id)
        if status == "BLOCKED":
            return False, f"Action Gateway Policy Block: {reason}"

        # 4. Map and route execution to existing services
        try:
            if action == "DISCOVER_JOBS":
                from app.services.job_discovery_service import JobDiscoveryService
                res = JobDiscoveryService.run_discovery_all_enabled(db, limit_per_source=10)
                return True, f"Jobs discovery executed successfully: {res}"

            elif action == "CREATE_PACKAGE":
                if not job_id:
                    return False, "Job ID required to prepare application package."
                from app.services.tailoring.package_service import ApplicationPackageService
                from app.services.tailoring.resume_tailoring_service import ResumeTailoringService
                from app.models.resume import Resume
                from app.models.job import Job
                from app.models.profile import UserProfile
                
                profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
                job = db.query(Job).filter(Job.id == job_id).first()
                resume = db.query(Resume).filter(Resume.profile_id == profile_id, Resume.is_default == True).first()

                tailored = ResumeTailoringService.tailor_resume(db, profile, job, master_resume=resume)
                tailored.status = "VALIDATED"
                db.commit()

                package = ApplicationPackageService.create_package(
                    db, profile_id, job_id,
                    source_resume_id=resume.id if resume else None,
                    tailored_resume_id=tailored.id if tailored else None
                )

                # Initialize application state
                from app.models.application import Application
                app_rec = Application(
                    profile_id=profile_id,
                    job_id=job_id,
                    application_package_id=package.id,
                    source=job.source.name if job and job.source else "mock",
                    application_url=job.application_url or (job.job_url if job else None),
                    status="PREPARING",
                    selected_resume_id=resume.id if resume else None,
                    tailored_resume_id=tailored.id if tailored else None,
                    primary_mission_id=mission_id
                )
                db.add(app_rec)
                db.commit()
                return True, f"Application package created with ID {package.id}."

            elif action == "REQUEST_REVIEW":
                from app.models.application import Application
                app_rec = db.query(Application).filter(
                    Application.profile_id == profile_id,
                    Application.job_id == job_id
                ).first()
                if app_rec:
                    app_rec.status = "READY_FOR_REVIEW"
                    db.commit()
                    return True, "Application review requested successfully."
                return False, "Application not found."

            elif action == "EXECUTE_PERMITTED_APPLICATION":
                from app.services.submission.submission_engine import SubmissionEngine
                from app.models.application import Application
                app_rec = db.query(Application).filter(
                    Application.profile_id == profile_id,
                    Application.job_id == job_id
                ).first()
                if app_rec:
                    run = SubmissionEngine.submit_application(db, app_rec.id)
                    return True, f"Application execution completed. Run ID: {run.id} Status: {run.status}."
                return False, "Application not found."

            elif action == "START_HUMAN_ASSISTED_SESSION":
                # Create a human intervention event task
                from app.models.application import HumanInterventionEvent
                event = HumanInterventionEvent(
                    profile_id=profile_id,
                    application_id=None,
                    intervention_type="CAPTCHA_OR_LOGIN",
                    status="PENDING",
                    message="Manual login or CAPTCHA resolution required on destination portal."
                )
                db.add(event)
                db.commit()
                return True, f"Human intervention session registered. Event ID: {event.id}"

            # General mock actions
            return True, f"Gateway executed whitelisted operation '{action}'."

        except Exception as e:
            return False, f"Action Gateway Execution Error: {str(e)}"

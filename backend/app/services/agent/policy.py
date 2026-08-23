from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.profile import UserProfile
from app.models.job import Job
from app.models.mission import JobSearchMission
from app.models.application import Application, SubmissionAuthorization
from app.services.orchestration.orchestrator import JobPilotOrchestrator


class AgentPolicyEngine:
    """
    Enforces hierarchical checks:
    GLOBAL SAFETY -> ACCOUNT POLICY -> MISSION POLICY -> JOB POLICY -> AGENT DECISION.
    Ensures that a lower policy level cannot expand permissions, only restrict them.
    """

    @staticmethod
    def validate_action(
        db: Session,
        profile_id: int,
        action: str,
        job_id: Optional[int] = None,
        mission_id: Optional[int] = None
    ) -> Tuple[str, str]:
        """
        Validates whether an action is ALLOWED, BLOCKED, or REQUIRES_HUMAN.
        Returns (status, reason).
        """
        # 1. Global Safety Policy (Explicit domain whitelist restriction)
        if action in ["EXECUTE_PERMITTED_APPLICATION", "START_HUMAN_ASSISTED_SESSION"]:
            if job_id:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job and job.application_url:
                    domain = job.application_url.split("//")[-1].split("/")[0]
                    allowed_domains = ["localhost", "127.0.0.1", "greenhouse.io", "lever.co"]
                    if not any(d in domain for d in allowed_domains):
                        return "BLOCKED", f"Global Safety: domain '{domain}' not in allowed list."

        # 2. Account Limits Validation
        if action in ["EXECUTE_PERMITTED_APPLICATION", "QUEUE_APPLICATION"]:
            global_config = JobPilotOrchestrator.get_or_create_config(db, profile_id)
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = db.query(Application).filter(
                Application.profile_id == profile_id,
                Application.created_at >= today_start,
                Application.status.in_(["SUBMITTED", "APPROVED", "SUBMITTING"])
            ).count()

            if today_count >= global_config.max_applications_per_day:
                return "BLOCKED", f"Account Policy: Daily limit ({global_config.max_applications_per_day}) exceeded."

        # 3. Mission Limits Validation
        if mission_id and action in ["EXECUTE_PERMITTED_APPLICATION", "QUEUE_APPLICATION"]:
            mission = db.query(JobSearchMission).filter(JobSearchMission.id == mission_id).first()
            if mission:
                mission_limits = mission.limits or {}
                max_day = mission_limits.get("max_applications_per_day", 5)
                
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                mission_today_count = db.query(Application).filter(
                    Application.primary_mission_id == mission_id,
                    Application.created_at >= today_start
                ).count()

                if mission_today_count >= max_day:
                    return "BLOCKED", f"Mission Policy: Mission daily limit ({max_day}) exceeded."

        # 4. Job specific checks: Approval & Authorization checks
        if action == "EXECUTE_PERMITTED_APPLICATION":
            if not job_id:
                return "BLOCKED", "Job ID missing for execution action."

            app_rec = db.query(Application).filter(
                Application.profile_id == profile_id,
                Application.job_id == job_id
            ).first()

            if not app_rec:
                return "BLOCKED", "Job Policy: Application record does not exist."

            if app_rec.status not in ["APPROVED", "SUBMITTED"]:
                return "BLOCKED", f"Job Policy: Human approval missing (current status: '{app_rec.status}')."

            # Check time-bound submission authorization
            auth = db.query(SubmissionAuthorization).filter(
                SubmissionAuthorization.application_id == app_rec.id,
                SubmissionAuthorization.status == "ACTIVE"
            ).order_by(SubmissionAuthorization.expires_at.desc()).first()

            if not auth or auth.expires_at < datetime.now():
                return "BLOCKED", "Job Policy: Submission authorization missing or expired."

        return "ALLOWED", "All policy criteria satisfied."

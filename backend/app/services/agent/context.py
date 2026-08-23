from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.models.job import Job
from app.models.mission import JobSearchMission
from app.models.application import Application
from app.models.resume import Resume
from app.models.personalization import PersonalPreferenceProfile
from app.services.orchestration.orchestrator import JobPilotOrchestrator
from app.services.orchestration.selection_service import JobSelectionService


class AgentContextBuilder:
    """
    Consolidates User, Job, Mission, Application, Platform, and System details.
    Builds context snapshots and versions.
    """

    @staticmethod
    def build_context(
        db: Session,
        profile_id: int,
        job_id: Optional[int] = None,
        mission_id: Optional[int] = None
    ) -> Dict[str, Any]:
        # 1. Fetch User Profile & Preferences
        profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        preferences = None
        resume = None
        if profile:
            preferences = db.query(PersonalPreferenceProfile).filter(
                PersonalPreferenceProfile.profile_id == profile_id
            ).first()
            resume = db.query(Resume).filter(
                Resume.profile_id == profile_id,
                Resume.is_default == True
            ).first()

        # 2. Fetch Job
        job = None
        if job_id:
            job = db.query(Job).filter(Job.id == job_id).first()

        # 3. Fetch Mission
        mission = None
        if mission_id:
            mission = db.query(JobSearchMission).filter(JobSearchMission.id == mission_id).first()
        else:
            # Check for any active mission
            mission = db.query(JobSearchMission).filter(
                JobSearchMission.profile_id == profile_id,
                JobSearchMission.status == "ACTIVE"
            ).first()

        # 4. Fetch Application details
        application = None
        history_status = "NONE"
        if profile_id and job_id:
            application = db.query(Application).filter(
                Application.profile_id == profile_id,
                Application.job_id == job_id
            ).first()
            
            # Determine selection history status
            if job:
                global_config = JobPilotOrchestrator.get_or_create_config(db, profile_id)
                history_status = JobSelectionService.get_application_history_status(
                    db, profile_id, job, cooldown_days=global_config.cooldown_days
                )

        # 5. Determine Platform Capabilities
        platform_capabilities = {
            "supports_automation": False,
            "requires_auth": True,
            "has_captcha": False
        }
        if job:
            src_name = ""
            if job.source:
                src_name = job.source.name.lower() if hasattr(job.source, "name") else str(job.source).lower()
            url_str = (job.job_url or "").lower()
            if "greenhouse" in src_name or "lever" in src_name or "mock" in src_name or "greenhouse" in url_str or "lever" in url_str:
                platform_capabilities["supports_automation"] = True
                platform_capabilities["requires_auth"] = False

        # 6. Fetch System config
        global_config = JobPilotOrchestrator.get_or_create_config(db, profile_id)
        system_limits = {
            "max_applications_per_day": global_config.max_applications_per_day,
            "cooldown_days": global_config.cooldown_days,
            "allowed_domains": ["localhost", "127.0.0.1", "greenhouse.io", "lever.co"]
        }

        # 7. Compile Decision Context Snapshot Versions
        snapshot = {
            "profile_version": getattr(profile, "updated_at", None).isoformat() if profile and getattr(profile, "updated_at", None) else "1.0",
            "job_version": getattr(job, "updated_at", None).isoformat() if job and getattr(job, "updated_at", None) else "1.0",
            "mission_version": mission.configuration_version if mission else 0,
            "package_version": getattr(application.package, "version", 1) if application and application.package else 1,
            "source_capability_version": 1,
            "configuration_version": 1
        }

        return {
            "profile": profile,
            "preferences": preferences,
            "resume": resume,
            "job": job,
            "mission": mission,
            "application": application,
            "history_status": history_status,
            "platform_capabilities": platform_capabilities,
            "system_limits": system_limits,
            "snapshot": snapshot
        }

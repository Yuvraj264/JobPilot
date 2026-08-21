from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.matching import JobMatch
from app.models.application import Application, ApplicationQueue, SubmissionRun
from app.models.orchestration import AutomationConfiguration

logger = logging.getLogger(__name__)


class JobSelectionService:
    """
    Evaluates jobs for selection, duplicate checking, daily constraints, cooldowns, and per-source limits.
    """

    @classmethod
    def get_application_history_status(
        cls,
        db: Session,
        profile_id: int,
        job: Job,
        cooldown_days: int = 30
    ) -> str:
        """
        Scans application history to prevent duplicate submissions or enforce cooldown limits.
        """
        # 1. Exact job matching
        existing = db.query(Application).filter(
            Application.profile_id == profile_id,
            Application.job_id == job.id
        ).first()

        if existing:
            if existing.status == "SUBMITTED":
                return "ALREADY_APPLIED"
            elif existing.status in ["PREPARING", "APPROVED", "SUBMISSION_AUTHORIZED", "SUBMITTING", "PAUSED"]:
                return "ALREADY_IN_PROGRESS"
            elif existing.status == "FAILED":
                # Check cooldown for failed applications
                if existing.updated_at and existing.updated_at > datetime.now() - timedelta(days=cooldown_days):
                    return "PREVIOUSLY_FAILED"
            elif existing.status == "REJECTED":
                return "PREVIOUSLY_REJECTED"

        # 2. Match by external job id or URL
        if job.external_job_id or job.application_url or job.job_url:
            filters = []
            if job.external_job_id:
                filters.append(Job.external_job_id == job.external_job_id)
            if job.application_url:
                filters.append(Job.application_url == job.application_url)
            if job.job_url:
                filters.append(Job.job_url == job.job_url)

            cross_job = db.query(Application).join(Job).filter(
                Application.profile_id == profile_id,
                *filters
            ).first()

            if cross_job:
                if cross_job.status == "SUBMITTED":
                    return "ALREADY_APPLIED"
                return "ALREADY_IN_PROGRESS"

        # 3. Match by Company Name + Title (Fuzzy check for potential duplicate)
        if job.company_name and job.title:
            title_clean = job.title.strip().lower()
            company_clean = job.company_name.strip().lower()

            fuzzy_matches = db.query(Application).join(Job).filter(
                Application.profile_id == profile_id,
                func.lower(Job.company_name) == company_clean,
                func.lower(Job.title) == title_clean
            ).all()

            for match in fuzzy_matches:
                if match.status == "SUBMITTED":
                    # If applied within the cooldown window, block
                    if match.submitted_at and match.submitted_at > datetime.now() - timedelta(days=cooldown_days):
                        return "ALREADY_APPLIED"
                    return "POTENTIAL_DUPLICATE"
                elif match.status in ["PREPARING", "APPROVED", "SUBMISSION_AUTHORIZED", "SUBMITTING", "PAUSED"]:
                    return "ALREADY_IN_PROGRESS"

        return "NOT_APPLIED"

    @classmethod
    def check_daily_limits_reached(
        cls,
        db: Session,
        profile_id: int,
        config: AutomationConfiguration,
        source_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifies profile-wide and per-source daily submission limits.
        """
        # Total applications submitted today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_today = db.query(Application).filter(
            Application.profile_id == profile_id,
            Application.status == "SUBMITTED",
            Application.submitted_at >= today_start
        ).count()

        if total_today >= config.max_applications_per_day:
            return {"reached": True, "reason": f"Profile daily limit of {config.max_applications_per_day} reached."}

        # Source specific limits check
        if source_name:
            source_clean = source_name.lower()
            
            # Fetch custom source configurations
            from app.models.application import ApplicationSourceConfiguration, JobSource
            source_rec = db.query(JobSource).filter(JobSource.name == source_clean).first()
            if source_rec:
                src_cfg = db.query(ApplicationSourceConfiguration).filter(
                    ApplicationSourceConfiguration.source_id == source_rec.id
                ).first()
                
                if src_cfg:
                    # Applications submitted per source today
                    source_today = db.query(Application).filter(
                        Application.profile_id == profile_id,
                        Application.status == "SUBMITTED",
                        Application.submitted_at >= today_start,
                        func.lower(Application.source) == source_clean
                    ).count()

                    if source_today >= src_cfg.max_applications_per_day:
                        return {"reached": True, "reason": f"Per-source daily limit of {src_cfg.max_applications_per_day} reached for '{source_clean}'."}

        return {"reached": False}

    @classmethod
    def select_jobs_for_orchestration(
        cls,
        db: Session,
        profile_id: int,
        config: AutomationConfiguration
    ) -> List[Job]:
        """
        Identifies and filters eligible high-match jobs for processing.
        """
        # Fetch best active matches
        matches = db.query(JobMatch).filter(
            JobMatch.profile_id == profile_id,
            JobMatch.overall_score >= config.minimum_match_score,
            JobMatch.recommendation.in_(config.allowed_recommendations)
        ).all()

        selected_jobs = []
        for match in matches:
            job = match.job
            if not job or job.status not in ["ACTIVE", "DISCOVERED"]:
                continue

            # Verify history & duplicates
            history_status = cls.get_application_history_status(
                db, profile_id, job, cooldown_days=config.cooldown_days
            )

            # Accidental duplicate avoidance
            if history_status in ["ALREADY_APPLIED", "ALREADY_IN_PROGRESS", "PREVIOUSLY_FAILED", "PREVIOUSLY_REJECTED"]:
                logger.info(f"Skipping job {job.id} - duplicate check result: {history_status}")
                continue

            selected_jobs.append(job)

        return selected_jobs

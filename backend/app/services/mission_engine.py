import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.profile import UserProfile, Skill
from app.models.job import Job
from app.models.matching import JobMatch, MatchConfig
from app.models.application import Application, ApplicationQueue, SubmissionAuthorization
from app.models.mission import JobSearchMission, MissionRun, MissionAuditLog
from app.services.job_discovery_service import JobDiscoveryService
from app.services.job_matching_service import JobMatchingService
from app.services.orchestration.selection_service import JobSelectionService
from app.services.tailoring.resume_tailoring_service import ResumeTailoringService
from app.services.tailoring.package_service import ApplicationPackageService
from app.services.application.validation_service import ApplicationValidationService
from app.services.orchestration.orchestrator import JobPilotOrchestrator

logger = logging.getLogger(__name__)


class MissionEngine:
    """
    Coordinates loading, configuring, validating, running, and diagnosing JobSearchMissions.
    """

    @classmethod
    def validate_configuration(cls, db: Session, mission: JobSearchMission) -> Dict[str, Any]:
        """
        Validates target roles, limits, date boundaries, and checks for conflicting preferences.
        """
        errors = []
        warnings = []

        profile = db.query(UserProfile).filter(UserProfile.id == mission.profile_id).first()
        if not profile:
            errors.append("User profile not found")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # 1. Contradictory Filters conflict detection
        global_prefs = getattr(profile, "personal_preference_profile", None)
        if global_prefs and global_prefs.enabled:
            # Remote-only (global) vs Onsite-only (mission)
            global_modes = [w.get("value", "").upper() for w in global_prefs.workplace_modes if w.get("type") != "disliked"]
            mission_modes = [m.upper() for m in mission.objective.get("target_work_modes", [])]
            if "REMOTE" in global_modes and "ONSITE" in mission_modes and len(mission_modes) == 1:
                warnings.append("Mission conflicts with your global preference. Global preference is Remote-only but Mission specifies Onsite.")

        # 2. Date intervals validation
        if mission.start_date and mission.end_date and mission.start_date > mission.end_date:
            errors.append("Mission end date cannot be earlier than start date.")

        # 3. Limit validation against global settings
        global_config = JobPilotOrchestrator.get_or_create_config(db, mission.profile_id)
        mission_limits = mission.limits or {}
        if mission_limits.get("max_applications_per_day", 0) > global_config.max_applications_per_day:
            errors.append(f"Mission limits exceed global limits. Max applications per day ({mission_limits.get('max_applications_per_day')}) cannot exceed global daily limit ({global_config.max_applications_per_day}).")

        # 4. Sources validation
        sources_cfg = mission.source_configuration or {}
        selected_sources = sources_cfg.get("selected_sources", [])
        if not sources_cfg.get("all_enabled_sources", True) and not selected_sources:
            errors.append("No active sources selected in mission configuration.")

        # 5. Salary range validation
        obj = mission.objective or {}
        if obj.get("salary_floor", 0) < 0:
            errors.append("Salary floor cannot be negative.")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    @classmethod
    def calculate_mission_fit(cls, job: Job, mission: JobSearchMission) -> Dict[str, Any]:
        """
        Computes relevance, checking target roles, locations, skills, and experience constraints.
        """
        explanation = []
        obj = mission.objective or {}
        
        # Exclusions (Hard filters)
        excluded_titles = obj.get("excluded_titles", [])
        title_lower = (job.title or "").lower()
        for et in excluded_titles:
            if et.lower() in title_lower:
                explanation.append(f"✗ Excluded title keyword matched: '{et}'")
                return {"score": 0.0, "explanation": explanation, "fit": False}

        excluded_companies = obj.get("excluded_companies", [])
        company_lower = (job.company_name or "").lower()
        for ec in excluded_companies:
            if ec.lower() in company_lower:
                explanation.append(f"✗ Excluded company name matched: '{ec}'")
                return {"score": 0.0, "explanation": explanation, "fit": False}

        # Role Fit
        target_roles = obj.get("target_roles", [])
        role_fit = 0.0
        if target_roles:
            matched_role = None
            for r in target_roles:
                if r.lower() in title_lower:
                    matched_role = r
                    role_fit = 100.0
                    break
            if role_fit > 0:
                explanation.append(f"✓ {matched_role} is a target role")
            else:
                explanation.append("✗ Title does not match target roles")
                return {"score": 0.0, "explanation": explanation, "fit": False}
        else:
            role_fit = 100.0
            explanation.append("✓ Target roles match (none defined)")

        # Location Fit
        target_locations = obj.get("target_locations", [])
        location_fit = 0.0
        job_loc_lower = (job.location or "").lower()
        if target_locations:
            matched_loc = None
            for loc in target_locations:
                if loc.lower() in job_loc_lower:
                    matched_loc = loc
                    location_fit = 100.0
                    break
            if location_fit > 0:
                explanation.append(f"✓ {matched_loc} matches mission location")
            else:
                explanation.append("✗ Location does not match target locations")
                return {"score": 0.0, "explanation": explanation, "fit": False}
        else:
            location_fit = 100.0
            explanation.append("✓ Location matches (none defined)")

        # Skill Fit
        pref_skills = obj.get("preferred_skills", [])
        desc_lower = (job.description or "").lower()
        matched_skills = []
        for s in pref_skills:
            if s.lower() in desc_lower:
                matched_skills.append(s)
        if matched_skills:
            explanation.extend([f"✓ {s} matches preferred skill" for s in matched_skills])
            
        skill_score = (len(matched_skills) / max(1, len(pref_skills))) * 100.0 if pref_skills else 100.0

        # Overall weighted score
        overall_score = round((role_fit * 0.4 + location_fit * 0.4 + skill_score * 0.2) / 100.0, 2)
        
        return {
            "score": overall_score,
            "explanation": explanation,
            "fit": overall_score >= 0.5
        }

    @classmethod
    def run_mission(cls, db: Session, mission_id: int, trigger_type: str = "MANUAL") -> MissionRun:
        """
        Executes end-to-end execution window run targeting active mission specifications.
        """
        mission = db.query(JobSearchMission).filter(JobSearchMission.id == mission_id).first()
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")

        # Expiration logic
        if mission.end_date and datetime.now() > mission.end_date:
            mission.status = "EXPIRED"
            db.commit()
            logger.info(f"Mission {mission_id} has expired and will not execute.")
            expired_run = MissionRun(mission_id=mission_id, status="FAILED", errors=["Mission has expired."])
            db.add(expired_run)
            db.commit()
            return expired_run

        if mission.status != "ACTIVE":
            logger.warning(f"Mission {mission_id} is not in ACTIVE state. Aborting run.")
            inactive_run = MissionRun(mission_id=mission_id, status="FAILED", errors=["Mission is not active."])
            db.add(inactive_run)
            db.commit()
            return inactive_run

        run = MissionRun(mission_id=mission_id, status="RUNNING")
        db.add(run)
        db.commit()
        db.refresh(run)

        try:
            # 1. Job Ingestion / Discovery
            sources_cfg = mission.source_configuration or {}
            max_jobs = mission.limits.get("max_jobs_per_run", 10) if mission.limits else 10
            
            discovery_results = JobDiscoveryService.run_discovery_all_enabled(
                db, limit_per_source=max_jobs
            )
            run.jobs_discovered = sum(r.get("jobs_discovered", 0) for r in discovery_results if r.get("status") != "FAILED")
            db.commit()

            # 2. Match calculations
            match_run = JobMatchingService.run_batch_matching(db, mission.profile_id, limit=50)
            run.jobs_eligible = match_run.jobs_evaluated
            db.commit()

            # 3. Selection
            # Find eligible job match items
            min_score = mission.objective.get("minimum_match_score", 70.0)
            matches = db.query(JobMatch).filter(
                JobMatch.profile_id == mission.profile_id,
                JobMatch.overall_score >= min_score
            ).all()

            selected_jobs = []
            for match in matches:
                job = match.job
                if not job or job.status not in ["ACTIVE", "DISCOVERED"]:
                    continue

                # Exclusions
                fit_eval = cls.calculate_mission_fit(job, mission)
                if not fit_eval["fit"]:
                    continue

                # Duplicate / cooldown check
                global_config = JobPilotOrchestrator.get_or_create_config(db, mission.profile_id)
                hist_status = JobSelectionService.get_application_history_status(
                    db, mission.profile_id, job, cooldown_days=global_config.cooldown_days
                )
                if hist_status in ["ALREADY_APPLIED", "ALREADY_IN_PROGRESS"]:
                    continue

                selected_jobs.append((job, match, fit_eval))

            run.jobs_selected = len(selected_jobs)
            db.commit()

            # 4. Limit budget gate check
            budget_limit = mission.limits.get("max_applications_per_run", 3) if mission.limits else 3
            day_limit = mission.limits.get("max_applications_per_day", 5) if mission.limits else 5
            
            # Count today's apps under mission context
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = db.query(Application).filter(
                Application.primary_mission_id == mission_id,
                Application.created_at >= today_start
            ).count()

            # 5. Application Package Preparation Loop
            prepared_count = 0
            for job, match, fit_eval in selected_jobs:
                if prepared_count >= budget_limit or (today_count + prepared_count) >= day_limit:
                    logger.info(f"Daily or run budget limit reached for mission {mission_id}.")
                    break

                try:
                    # Retrieve profile default resume
                    from app.models.resume import Resume
                    master_res = db.query(Resume).filter(
                        Resume.profile_id == mission.profile_id,
                        Resume.is_default == True
                    ).first()

                    # Tailor package
                    tailored = ResumeTailoringService.tailor_resume(db, mission.profile, job, master_resume=master_res)
                    tailored.status = "VALIDATED"
                    db.commit()

                    package = ApplicationPackageService.create_package(
                        db, mission.profile_id, job.id,
                        source_resume_id=master_res.id if master_res else None,
                        tailored_resume_id=tailored.id if tailored else None
                    )

                    # Initialize Application referencing mission attribution ID
                    app_rec = Application(
                        profile_id=mission.profile_id,
                        job_id=job.id,
                        application_package_id=package.id,
                        source=job.source.name if job.source else "mock",
                        application_url=job.application_url or job.job_url,
                        status="PREPARING",
                        selected_resume_id=master_res.id if master_res else None,
                        tailored_resume_id=tailored.id if tailored else None,
                        primary_mission_id=mission_id
                    )
                    db.add(app_rec)
                    db.commit()
                    db.refresh(app_rec)

                    # Validate application gate
                    val = ApplicationValidationService.validate_application(
                        db, job, mission.profile, master_res, tailored, package
                    )
                    if not val["valid"]:
                        app_rec.status = "FAILED"
                        app_rec.failure_reason = "Quality gate validation failed."
                        run.applications_failed += 1
                        db.commit()
                        continue

                    # Queue application based on strategy
                    strategy = mission.application_strategy
                    if strategy == "HUMAN_REVIEW":
                        app_rec.status = "READY_FOR_REVIEW"
                        db.commit()
                        run.applications_approved += 1
                    elif strategy == "SUPPORTED_AUTOMATIC":
                        app_rec.status = "APPROVED"
                        db.commit()
                        run.applications_approved += 1

                        auth = SubmissionAuthorization(
                            application_id=app_rec.id,
                            package_version=1,
                            status="ACTIVE",
                            expires_at=datetime.now() + timedelta(hours=24)
                        )
                        db.add(auth)

                        queue_rec = ApplicationQueue(
                            application_id=app_rec.id,
                            priority=match.overall_score * fit_eval["score"],
                            status="QUEUED"
                        )
                        db.add(queue_rec)
                        db.commit()

                    prepared_count += 1
                    run.applications_prepared += 1
                    db.commit()

                except Exception as prep_err:
                    logger.error(f"Failed application generation in mission run: {prep_err}")
                    run.applications_failed += 1
                    run.errors = list(run.errors) + [str(prep_err)]
                    db.commit()

            run.status = "COMPLETED"
            run.completed_at = datetime.now()
            db.commit()

            # Aggregate diagnostics and feedback health
            cls.run_diagnostics_and_health(db, mission_id)

        except Exception as e:
            logger.error(f"Mission execution run {run.id} failed: {e}")
            run.status = "FAILED"
            run.completed_at = datetime.now()
            run.errors = list(run.errors) + [str(e)]
            db.commit()

        return run

    @classmethod
    def run_diagnostics_and_health(cls, db: Session, mission_id: int):
        """
        Updates mission status diagnostic warning strings and suggested parameters adjustments.
        """
        mission = db.query(JobSearchMission).filter(JobSearchMission.id == mission_id).first()
        if not mission:
            return

        latest_run = db.query(MissionRun).filter(
            MissionRun.mission_id == mission_id
        ).order_by(MissionRun.started_at.desc()).first()

        diag = {}
        health = "HEALTHY"

        if latest_run:
            if latest_run.jobs_discovered > 0 and latest_run.jobs_selected == 0:
                health = "NO_MATCHES"
                diag["reason"] = f"Mission discovered {latest_run.jobs_discovered} jobs, but 0 met eligibility / match thresholds."
                diag["suggestion"] = "Lower the minimum match score configuration threshold."
            elif latest_run.applications_failed > 0:
                health = "HIGH_FAILURE_RATE"
                diag["reason"] = f"Run encountered {latest_run.applications_failed} preparation quality gate failures."
                diag["suggestion"] = "Verify profile details completeness."

        mission.health = health
        mission.diagnostics = diag
        db.commit()

    @classmethod
    def log_audit(cls, db: Session, mission_id: int, old_config: dict, new_config: dict, version: int):
        """
        Saves snapshot adjustments records.
        """
        changes = {}
        for k, v in new_config.items():
            old_val = old_config.get(k)
            if old_val != v:
                changes[k] = {"old": old_val, "new": v}

        if changes:
            log = MissionAuditLog(
                mission_id=mission_id,
                changes=changes,
                configuration_version=version
            )
            db.add(log)
            db.commit()

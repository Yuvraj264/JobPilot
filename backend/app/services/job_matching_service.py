from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.profile import UserProfile
from app.models.job import Job
from app.models.matching import JobMatch, MatchRun, MatchConfig
from app.services.matching.scoring_engine import ScoringEngine


class JobMatchingService:
    """
    Service Layer for Single & Batch Job Evaluation, Match Database Persistence, and Config Management.
    """

    @staticmethod
    def get_or_create_config(db: Session, profile_id: int) -> MatchConfig:
        config = db.query(MatchConfig).filter(MatchConfig.profile_id == profile_id).first()
        if not config:
            config = MatchConfig(
                profile_id=profile_id,
                weight_skills=0.35,
                weight_role=0.20,
                weight_experience=0.15,
                weight_location=0.10,
                weight_workplace=0.05,
                weight_employment=0.05,
                weight_education=0.05,
                weight_semantic=0.05,
                threshold_apply=85.0,
                threshold_review=70.0,
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        return config

    @staticmethod
    def match_single_job(db: Session, job_id: int, profile_id: int) -> JobMatch:
        profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        if not profile:
            raise ValueError(f"UserProfile with ID {profile_id} not found.")

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job with ID {job_id} not found.")

        config = JobMatchingService.get_or_create_config(db, profile_id)
        eval_res = ScoringEngine.evaluate_job(profile, job, config)

        match_rec = db.query(JobMatch).filter(
            JobMatch.job_id == job_id,
            JobMatch.profile_id == profile_id,
        ).first()

        if not match_rec:
            match_rec = JobMatch(
                job_id=job.id,
                profile_id=profile.id,
                overall_score=eval_res["overall_score"],
                recommendation=eval_res["recommendation"],
                eligible=eval_res["eligible"],
                confidence=eval_res["confidence"],
                matcher_version="1.0",
                component_scores=eval_res["component_scores"],
                hard_failures=eval_res["hard_failures"],
                warnings=eval_res["warnings"],
                strengths=eval_res["strengths"],
                concerns=eval_res["concerns"],
                explanation=eval_res["explanation"],
            )
            db.add(match_rec)
        else:
            match_rec.overall_score = eval_res["overall_score"]
            match_rec.recommendation = eval_res["recommendation"]
            match_rec.eligible = eval_res["eligible"]
            match_rec.confidence = eval_res["confidence"]
            match_rec.component_scores = eval_res["component_scores"]
            match_rec.hard_failures = eval_res["hard_failures"]
            match_rec.warnings = eval_res["warnings"]
            match_rec.strengths = eval_res["strengths"]
            match_rec.concerns = eval_res["concerns"]
            match_rec.explanation = eval_res["explanation"]
            match_rec.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(match_rec)
        return match_rec

    @staticmethod
    def run_batch_matching(db: Session, profile_id: int, limit: int = 100) -> MatchRun:
        profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        if not profile:
            raise ValueError(f"UserProfile with ID {profile_id} not found.")

        # Start Audit Run
        match_run = MatchRun(
            profile_id=profile.id,
            started_at=datetime.now(timezone.utc),
            status="RUNNING",
        )
        db.add(match_run)
        db.commit()
        db.refresh(match_run)

        try:
            # Query active/discovered jobs
            jobs = db.query(Job).filter(
                Job.status.in_(["DISCOVERED", "ACTIVE", "POTENTIAL_DUPLICATE"])
            ).order_by(Job.id.desc()).limit(limit).all()

            config = JobMatchingService.get_or_create_config(db, profile_id)

            eval_count = 0
            eligible_count = 0
            apply_cnt = 0
            review_cnt = 0
            skip_cnt = 0
            err_cnt = 0

            for job in jobs:
                try:
                    match_rec = JobMatchingService.match_single_job(db, job.id, profile.id)
                    eval_count += 1
                    if match_rec.eligible:
                        eligible_count += 1
                    if match_rec.recommendation == "APPLY":
                        apply_cnt += 1
                    elif match_rec.recommendation == "REVIEW":
                        review_cnt += 1
                    else:
                        skip_cnt += 1
                except Exception as ex:
                    err_cnt += 1
                    print(f"Error matching job {job.id}: {ex}")

            match_run.status = "COMPLETED" if err_cnt == 0 else "PARTIAL"
            match_run.completed_at = datetime.now(timezone.utc)
            match_run.jobs_evaluated = eval_count
            match_run.jobs_eligible = eligible_count
            match_run.apply_count = apply_cnt
            match_run.review_count = review_cnt
            match_run.skip_count = skip_cnt
            match_run.error_count = err_cnt
            db.commit()
            db.refresh(match_run)
            return match_run

        except Exception as run_err:
            db.rollback()
            match_run.status = "FAILED"
            match_run.completed_at = datetime.now(timezone.utc)
            match_run.error_message = str(run_err)
            db.commit()
            raise run_err

    @staticmethod
    def get_matching_stats(db: Session, profile_id: int) -> Dict[str, Any]:
        total_eval = db.query(JobMatch).filter(JobMatch.profile_id == profile_id).count()
        eligible = db.query(JobMatch).filter(JobMatch.profile_id == profile_id, JobMatch.eligible == True).count()
        apply_cnt = db.query(JobMatch).filter(JobMatch.profile_id == profile_id, JobMatch.recommendation == "APPLY").count()
        review_cnt = db.query(JobMatch).filter(JobMatch.profile_id == profile_id, JobMatch.recommendation == "REVIEW").count()
        skip_cnt = db.query(JobMatch).filter(JobMatch.profile_id == profile_id, JobMatch.recommendation == "SKIP").count()

        avg_score = db.query(func.avg(JobMatch.overall_score)).filter(JobMatch.profile_id == profile_id).scalar() or 0.0

        return {
            "jobs_evaluated": total_eval,
            "eligible": eligible,
            "apply": apply_cnt,
            "review": review_cnt,
            "skip": skip_cnt,
            "average_score": round(float(avg_score), 2),
        }

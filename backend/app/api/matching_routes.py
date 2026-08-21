from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.profile_service import ProfileService
from app.services.job_matching_service import JobMatchingService
from app.models.matching import JobMatch, MatchRun, MatchConfig
from app.schemas.matching import (
    JobMatchResponse,
    JobMatchDetailResponse,
    MatchRunResponse,
    MatchConfigResponse,
    MatchConfigUpdate,
    MatchStatsResponse,
    BatchMatchRequest,
)

router = APIRouter(prefix="/api/matching", tags=["Job Matching & Intelligent Selection"])


@router.post("/job/{job_id}", response_model=JobMatchDetailResponse)
def evaluate_single_job(job_id: int, db: Session = Depends(get_db)):
    """Evaluate a single job against current user profile."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found. Please create a profile first.")

    try:
        match_rec = JobMatchingService.match_single_job(db, job_id=job_id, profile_id=profile.id)
        return match_rec
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))


@router.get("/job/{job_id}", response_model=JobMatchDetailResponse)
def get_job_match(job_id: int, db: Session = Depends(get_db)):
    """Retrieve existing match evaluation result for a job."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")

    match_rec = db.query(JobMatch).filter(
        JobMatch.job_id == job_id,
        JobMatch.profile_id == profile.id,
    ).first()

    if not match_rec:
        # Auto-run matching if not yet evaluated
        try:
            return JobMatchingService.match_single_job(db, job_id=job_id, profile_id=profile.id)
        except ValueError as err:
            raise HTTPException(status_code=404, detail=str(err))

    return match_rec


@router.get("/jobs", response_model=List[JobMatchDetailResponse])
def list_job_matches(
    recommendation: Optional[str] = Query(None, description="Filter by recommendation: APPLY, REVIEW, SKIP"),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0),
    eligible_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List evaluated job matches with filtering and pagination."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        return []

    query = db.query(JobMatch).filter(JobMatch.profile_id == profile.id)

    if recommendation:
        query = query.filter(JobMatch.recommendation == recommendation.upper())
    if min_score is not None:
        query = query.filter(JobMatch.overall_score >= min_score)
    if eligible_only:
        query = query.filter(JobMatch.eligible == True)

    return query.order_by(JobMatch.overall_score.desc()).offset(offset).limit(limit).all()


@router.post("/run", response_model=MatchRunResponse)
def run_batch_matching(body: Optional[BatchMatchRequest] = None, db: Session = Depends(get_db)):
    """Trigger batch matching run across all active jobs."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        # Auto-seed profile if unpopulated
        from app.services.seed_service import seed_sample_profile
        profile = seed_sample_profile(db, user_id=1)

    limit = body.limit if body else 100
    try:
        return JobMatchingService.run_batch_matching(db, profile_id=profile.id, limit=limit)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Batch matching run failed: {str(err)}")


@router.get("/runs", response_model=List[MatchRunResponse])
def list_match_runs(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Retrieve audit logs of historical batch matching runs."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        return []
    return db.query(MatchRun).filter(MatchRun.profile_id == profile.id).order_by(MatchRun.started_at.desc()).limit(limit).all()


@router.get("/runs/{id}", response_model=MatchRunResponse)
def get_match_run(id: int, db: Session = Depends(get_db)):
    """Retrieve details for a specific batch match run."""
    run = db.query(MatchRun).filter(MatchRun.id == id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Match run with ID {id} not found.")
    return run


@router.get("/stats", response_model=MatchStatsResponse)
def get_matching_stats(db: Session = Depends(get_db)):
    """Retrieve job matching dashboard metrics."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        return {
            "jobs_evaluated": 0,
            "eligible": 0,
            "apply": 0,
            "review": 0,
            "skip": 0,
            "average_score": 0.0,
        }
    return JobMatchingService.get_matching_stats(db, profile.id)


@router.get("/config", response_model=MatchConfigResponse)
def get_matching_config(db: Session = Depends(get_db)):
    """Retrieve matching scoring weights and thresholds configuration."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return JobMatchingService.get_or_create_config(db, profile.id)


@router.put("/config", response_model=MatchConfigResponse)
def update_matching_config(payload: MatchConfigUpdate, db: Session = Depends(get_db)):
    """Update matching scoring weights and recommendation thresholds."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")

    config = JobMatchingService.get_or_create_config(db, profile.id)

    if payload.weight_skills is not None: config.weight_skills = payload.weight_skills
    if payload.weight_role is not None: config.weight_role = payload.weight_role
    if payload.weight_experience is not None: config.weight_experience = payload.weight_experience
    if payload.weight_location is not None: config.weight_location = payload.weight_location
    if payload.weight_workplace is not None: config.weight_workplace = payload.weight_workplace
    if payload.weight_employment is not None: config.weight_employment = payload.weight_employment
    if payload.weight_education is not None: config.weight_education = payload.weight_education
    if payload.weight_semantic is not None: config.weight_semantic = payload.weight_semantic
    if payload.threshold_apply is not None: config.threshold_apply = payload.threshold_apply
    if payload.threshold_review is not None: config.threshold_review = payload.threshold_review

    db.commit()
    db.refresh(config)
    return config

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.profile_service import ProfileService
from app.services.application_agent import ApplicationAgent
from app.models.automation import AutomationRun, ActionLog
from app.models.job import Job
from app.schemas.automation import (
    AutomationRunResponse,
    AutomationRunDetailResponse,
    ActionLogResponse,
    AutomationStartRequest,
)

from app.api.auth import get_current_user_id

router = APIRouter(prefix="/api/automation", tags=["Application Automation Agent"])


@router.post("/run", response_model=AutomationRunResponse)
def start_automation_run(payload: AutomationStartRequest, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Start browser automation run against local mock application server."""
    profile = ProfileService.get_profile(db, user_id=current_user_id)
    if not profile:
        from app.services.seed_service import seed_sample_profile
        profile = seed_sample_profile(db, user_id=current_user_id)

    # Ensure synthetic mock job exists in database if job_id is 101
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job and payload.job_id == 101:
        from app.models.job import JobSource
        source = db.query(JobSource).filter(JobSource.name == "mock").first()
        source_id = source.id if source else None
        job = Job(
            id=101,
            source_id=source_id,
            external_job_id="MOCK-101",
            title="Junior QA Engineer",
            company_name="Acme Technologies",
            location="Bengaluru, India",
            normalized_location="Bengaluru, India",
            employment_type="FULL_TIME",
            workplace_type="HYBRID",
            description="Synthetic QA role requiring testing fundamentals, SQL, Selenium, and API testing.",
            status="ACTIVE"
        )
        db.add(job)
        db.commit()
        db.refresh(job)

    try:
        run = ApplicationAgent.start_automation(db, profile_id=profile.id, job_id=payload.job_id)
        return run
    except ValueError as val_err:
        raise HTTPException(status_code=404, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Automation run failed: {str(err)}")


@router.get("/runs", response_model=List[AutomationRunResponse])
def list_automation_runs(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """List historical automation runs."""
    profile = ProfileService.get_profile(db, user_id=current_user_id)
    if not profile:
        return []
    return db.query(AutomationRun).filter(AutomationRun.profile_id == profile.id).order_by(AutomationRun.started_at.desc()).limit(limit).all()


@router.get("/runs/{id}", response_model=AutomationRunDetailResponse)
def get_automation_run(id: int, db: Session = Depends(get_db)):
    """Retrieve details and action log timeline for a specific automation run."""
    run = db.query(AutomationRun).filter(AutomationRun.id == id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Automation run with ID {id} not found.")
    return run


@router.post("/runs/{id}/resume", response_model=AutomationRunResponse)
def resume_automation_run(id: int, db: Session = Depends(get_db)):
    """Resume a paused automation run after human intervention."""
    try:
        return ApplicationAgent.resume_automation(db, run_id=id)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@router.post("/runs/{id}/pause", response_model=AutomationRunResponse)
def pause_automation_run(id: int, reason: str = Query("User requested pause"), db: Session = Depends(get_db)):
    """Manually pause an active automation run."""
    try:
        return ApplicationAgent.pause_automation(db, run_id=id, reason=reason)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@router.get("/runs/{id}/actions", response_model=List[ActionLogResponse])
def get_run_action_logs(id: int, db: Session = Depends(get_db)):
    """Retrieve step-by-step action log entries for a run."""
    return db.query(ActionLog).filter(ActionLog.automation_run_id == id).order_by(ActionLog.id.asc()).all()


@router.get("/runs/{id}/screenshots")
def get_run_screenshots(id: int, db: Session = Depends(get_db)):
    """Retrieve captured screenshot metadata for an automation run."""
    run = db.query(AutomationRun).filter(AutomationRun.id == id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Automation run {id} not found.")
    return {"run_id": id, "screenshots": run.screenshots or []}

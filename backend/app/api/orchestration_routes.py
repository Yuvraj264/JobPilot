import threading
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.orchestration import OrchestrationRun, AutomationConfiguration
from app.schemas.orchestration import (
    OrchestrationRunResponse,
    AutomationConfigurationResponse,
    AutomationConfigurationUpdate,
    SchedulerStatusResponse,
    SchedulerConfigUpdate,
)
from app.services.orchestration.orchestrator import JobPilotOrchestrator
from app.services.orchestration.scheduler import AutomationScheduler
from app.services.orchestration.monitor import AutomationMonitor
from app.services.orchestration.analytics_service import AnalyticsService

from app.api.auth import get_current_user_id
from app.services.profile_service import ProfileService
from app.services.matching.career_insights import CareerInsights
from app.services.orchestration.optimization_engine import OptimizationEngine

router = APIRouter(tags=["Autonomous Orchestration & Scheduler System"])


def get_profile_id_by_user(db: Session, user_id: int) -> int:
    profile = ProfileService.get_profile(db, user_id=user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UserProfile not found. Please create a profile first."
        )
    return profile.id


@router.post("/api/orchestration/run", response_model=OrchestrationRunResponse)
def run_orchestration(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Triggers end-to-end autonomous pipeline execution in a background thread."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    active_run = db.query(OrchestrationRun).filter(
        OrchestrationRun.profile_id == profile_id,
        OrchestrationRun.status == "RUNNING"
    ).first()

    if active_run:
        return active_run

    run = OrchestrationRun(profile_id=profile_id, status="RUNNING", trigger_type="MANUAL")
    db.add(run)
    db.commit()
    db.refresh(run)

    # Spawn daemon execution thread
    threading.Thread(
        target=JobPilotOrchestrator.run_pipeline,
        args=(db, profile_id, "MANUAL", run.id),
        daemon=True
    ).start()

    return run


@router.post("/api/orchestration/stop")
def stop_orchestration(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Cancels a currently active pipeline run."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    active_run = db.query(OrchestrationRun).filter(
        OrchestrationRun.profile_id == profile_id,
        OrchestrationRun.status == "RUNNING"
    ).first()

    if not active_run:
        raise HTTPException(status_code=400, detail="No active orchestration run to stop.")

    JobPilotOrchestrator.stop_run(db, active_run.id)
    return {"success": True, "message": "Orchestration run stopped."}


@router.get("/api/orchestration/runs", response_model=List[OrchestrationRunResponse])
def get_orchestration_runs(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Retrieves list of historical orchestration runs."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    return db.query(OrchestrationRun).filter(OrchestrationRun.profile_id == profile_id).order_by(OrchestrationRun.started_at.desc()).all()


@router.get("/api/orchestration/runs/{id}", response_model=OrchestrationRunResponse)
def get_orchestration_run(id: int, db: Session = Depends(get_db)):
    """Retrieves details of a specific orchestration run."""
    run = db.query(OrchestrationRun).filter(OrchestrationRun.id == id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Orchestration run not found.")
    return run


@router.get("/api/orchestration/status")
def get_orchestration_status(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Returns active run status."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    run = db.query(OrchestrationRun).filter(
        OrchestrationRun.profile_id == profile_id,
        OrchestrationRun.status == "RUNNING"
    ).first()
    if run:
        return {"status": "RUNNING", "run_id": run.id}
    return {"status": "IDLE"}


@router.get("/api/orchestration/config", response_model=AutomationConfigurationResponse)
def get_orchestration_config(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Gets pipeline configuration limits and presets."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    return JobPilotOrchestrator.get_or_create_config(db, profile_id)


@router.put("/api/orchestration/config", response_model=AutomationConfigurationResponse)
def update_orchestration_config(payload: AutomationConfigurationUpdate, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Updates pipeline configuration limits and presets."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    config = JobPilotOrchestrator.get_or_create_config(db, profile_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(config, k, v)
    db.commit()
    db.refresh(config)
    return config


@router.get("/api/automation/health")
def get_automation_health(db: Session = Depends(get_db)):
    """Engine health status details check endpoint."""
    return AutomationMonitor.get_health_status(db)


@router.get("/api/analytics/overview")
def get_overview_analytics(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Gathers conversion metrics and today's activity overview counters."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    return AnalyticsService.get_overview_metrics(db, profile_id)


@router.get("/api/analytics/applications")
def get_applications_analytics(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Gathers applications statistics and source breakdowns."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    return AnalyticsService.get_applications_analytics(db, profile_id)


@router.get("/api/analytics/jobs")
def get_jobs_analytics(db: Session = Depends(get_db)):
    """Summarizes job counts by source, location, and workplace."""
    return AnalyticsService.get_jobs_analytics(db)


@router.get("/api/analytics/matching")
def get_matching_analytics(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Returns match score distribution charts metrics."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    return AnalyticsService.get_matching_analytics(db, profile_id)


@router.get("/api/analytics/failures")
def get_failures_analytics(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Groups run failures by cause categories."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    return AnalyticsService.get_failures_analytics(db, profile_id)


@router.get("/api/analytics/sources")
def get_sources_analytics(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Calculates success rates per source target."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    return AnalyticsService.get_sources_analytics(db, profile_id)


@router.get("/api/review/queue")
def get_review_queue(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Lists applications requiring manual human reviews or intervention resolves."""
    profile_id = get_profile_id_by_user(db, current_user_id)
    from app.models.application import Application
    return db.query(Application).filter(
        Application.profile_id == profile_id,
        Application.status.in_(["READY_FOR_REVIEW", "PAUSED", "REVIEW"])
    ).all()


@router.get("/api/scheduler/status", response_model=SchedulerStatusResponse)
def get_scheduler_status():
    """Gets run status metrics of the schedule engine."""
    return AutomationScheduler.get_status()


@router.post("/api/scheduler/start")
def start_scheduler():
    """Enables scheduling ticker thread."""
    AutomationScheduler.enabled = True
    AutomationScheduler.start()
    return {"success": True, "message": "Automation Scheduler started."}


@router.post("/api/scheduler/stop")
def stop_scheduler():
    """Disables scheduling ticker thread."""
    AutomationScheduler.enabled = False
    AutomationScheduler.stop()
    return {"success": True, "message": "Automation Scheduler stopped."}


@router.get("/api/scheduler/config", response_model=SchedulerStatusResponse)
def get_scheduler_config():
    """Gets current schedule configuration."""
    return AutomationScheduler.get_status()


@router.put("/api/scheduler/config", response_model=SchedulerStatusResponse)
def update_scheduler_config(payload: SchedulerConfigUpdate):
    """Updates schedule configuration parameters."""
    AutomationScheduler.update_config(payload.model_dump(exclude_unset=True))
    return AutomationScheduler.get_status()


@router.get("/api/analytics/career-insights")
def get_career_insights(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Retrieve career insights and requested/missing skill demand metrics."""
    profile = ProfileService.get_profile(db, user_id=current_user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return CareerInsights.get_insights(db, profile)


@router.get("/api/analytics/optimization-suggestions")
def get_optimization_suggestions(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Get actionable optimization suggestions for the profile based on previous runs."""
    profile = ProfileService.get_profile(db, user_id=current_user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return OptimizationEngine.get_suggestions(db, profile)


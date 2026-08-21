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

router = APIRouter(tags=["Autonomous Orchestration & Scheduler System"])


@router.post("/api/orchestration/run", response_model=OrchestrationRunResponse)
def run_orchestration(db: Session = Depends(get_db)):
    """Triggers end-to-end autonomous pipeline execution in a background thread."""
    active_run = db.query(OrchestrationRun).filter(
        OrchestrationRun.profile_id == 1,
        OrchestrationRun.status == "RUNNING"
    ).first()

    if active_run:
        return active_run

    run = OrchestrationRun(profile_id=1, status="RUNNING", trigger_type="MANUAL")
    db.add(run)
    db.commit()
    db.refresh(run)

    # Spawn daemon execution thread
    threading.Thread(
        target=JobPilotOrchestrator.run_pipeline,
        args=(db, 1, "MANUAL", run.id),
        daemon=True
    ).start()

    return run


@router.post("/api/orchestration/stop")
def stop_orchestration(db: Session = Depends(get_db)):
    """Cancels a currently active pipeline run."""
    active_run = db.query(OrchestrationRun).filter(
        OrchestrationRun.profile_id == 1,
        OrchestrationRun.status == "RUNNING"
    ).first()

    if not active_run:
        raise HTTPException(status_code=400, detail="No active orchestration run to stop.")

    JobPilotOrchestrator.stop_run(db, active_run.id)
    return {"success": True, "message": "Orchestration run stopped."}


@router.get("/api/orchestration/runs", response_model=List[OrchestrationRunResponse])
def get_orchestration_runs(db: Session = Depends(get_db)):
    """Retrieves list of historical orchestration runs."""
    return db.query(OrchestrationRun).filter(OrchestrationRun.profile_id == 1).order_by(OrchestrationRun.started_at.desc()).all()


@router.get("/api/orchestration/runs/{id}", response_model=OrchestrationRunResponse)
def get_orchestration_run(id: int, db: Session = Depends(get_db)):
    """Retrieves details of a specific orchestration run."""
    run = db.query(OrchestrationRun).filter(OrchestrationRun.id == id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Orchestration run not found.")
    return run


@router.get("/api/orchestration/status")
def get_orchestration_status(db: Session = Depends(get_db)):
    """Returns active run status."""
    run = db.query(OrchestrationRun).filter(
        OrchestrationRun.profile_id == 1,
        OrchestrationRun.status == "RUNNING"
    ).first()
    if run:
        return {"status": "RUNNING", "run_id": run.id}
    return {"status": "IDLE"}


@router.get("/api/orchestration/config", response_model=AutomationConfigurationResponse)
def get_orchestration_config(db: Session = Depends(get_db)):
    """Gets pipeline configuration limits and presets."""
    return JobPilotOrchestrator.get_or_create_config(db, 1)


@router.put("/api/orchestration/config", response_model=AutomationConfigurationResponse)
def update_orchestration_config(payload: AutomationConfigurationUpdate, db: Session = Depends(get_db)):
    """Updates pipeline configuration limits and presets."""
    config = JobPilotOrchestrator.get_or_create_config(db, 1)
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
def get_overview_analytics(db: Session = Depends(get_db)):
    """Gathers conversion metrics and today's activity overview counters."""
    return AnalyticsService.get_overview_metrics(db, 1)


@router.get("/api/analytics/applications")
def get_applications_analytics(db: Session = Depends(get_db)):
    """Gathers applications statistics and source breakdowns."""
    return AnalyticsService.get_applications_analytics(db, 1)


@router.get("/api/analytics/jobs")
def get_jobs_analytics(db: Session = Depends(get_db)):
    """Summarizes job counts by source, location, and workplace."""
    return AnalyticsService.get_jobs_analytics(db)


@router.get("/api/analytics/matching")
def get_matching_analytics(db: Session = Depends(get_db)):
    """Returns match score distribution charts metrics."""
    return AnalyticsService.get_matching_analytics(db, 1)


@router.get("/api/analytics/failures")
def get_failures_analytics(db: Session = Depends(get_db)):
    """Groups run failures by cause categories."""
    return AnalyticsService.get_failures_analytics(db, 1)


@router.get("/api/analytics/sources")
def get_sources_analytics(db: Session = Depends(get_db)):
    """Calculates success rates per source target."""
    return AnalyticsService.get_sources_analytics(db, 1)


@router.get("/api/review/queue")
def get_review_queue(db: Session = Depends(get_db)):
    """Lists applications requiring manual human reviews or intervention resolves."""
    from app.models.application import Application
    return db.query(Application).filter(
        Application.profile_id == 1,
        Application.status.in_(["READY_FOR_REVIEW", "PAUSED"])
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

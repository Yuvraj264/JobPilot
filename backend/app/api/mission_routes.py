from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database.connection import SessionLocal
from app.models.profile import UserProfile
from app.models.mission import JobSearchMission, MissionRun, MissionAuditLog
from app.models.application import Application
from app.services.mission_engine import MissionEngine
from datetime import datetime

router = APIRouter(prefix="/missions", tags=["Job Search Missions"])


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper to get current profile ID
def get_profile_id(db: Session, x_user_id: Optional[str]) -> int:
    if x_user_id:
        try:
            uid = int(x_user_id)
            profile = db.query(UserProfile).filter(UserProfile.user_id == uid).first()
            if profile:
                return profile.id
        except ValueError:
            pass
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile.id


# Pydantic Request Models
class MissionCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    objective: dict
    source_configuration: dict
    search_strategy: Optional[str] = "BALANCED"
    limits: dict
    scheduler_preset: dict
    application_strategy: Optional[str] = "HUMAN_REVIEW"
    application_budget: dict
    goal_configuration: dict


# --- REST Routes ---

@router.post("")
def create_mission(
    payload: MissionCreate,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    
    # Parse dates safely
    s_date = datetime.fromisoformat(payload.start_date) if payload.start_date else None
    e_date = datetime.fromisoformat(payload.end_date) if payload.end_date else None

    mission = JobSearchMission(
        profile_id=pid,
        name=payload.name,
        description=payload.description,
        status="DRAFT",
        start_date=s_date,
        end_date=e_date,
        objective=payload.objective,
        source_configuration=payload.source_configuration,
        search_strategy=payload.search_strategy,
        limits=payload.limits,
        scheduler_preset=payload.scheduler_preset,
        application_strategy=payload.application_strategy,
        application_budget=payload.application_budget,
        goal_configuration=payload.goal_configuration,
        configuration_version=1
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return {"message": "Mission draft created", "id": mission.id}


@router.get("")
def list_missions(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    missions = db.query(JobSearchMission).filter(JobSearchMission.profile_id == pid).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "status": m.status,
            "health": m.health,
            "goal_progress": m.goal_configuration.get("current_progress", 0.0),
            "configuration_version": m.configuration_version,
            "created_at": m.created_at
        }
        for m in missions
    ]


@router.get("/{id}")
def get_mission(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    mission = db.query(JobSearchMission).filter(JobSearchMission.id == id, JobSearchMission.profile_id == pid).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    return {
        "id": mission.id,
        "name": mission.name,
        "description": mission.description,
        "status": mission.status,
        "start_date": mission.start_date,
        "end_date": mission.end_date,
        "objective": mission.objective,
        "source_configuration": mission.source_configuration,
        "search_strategy": mission.search_strategy,
        "limits": mission.limits,
        "scheduler_preset": mission.scheduler_preset,
        "application_strategy": mission.application_strategy,
        "application_budget": mission.application_budget,
        "goal_configuration": mission.goal_configuration,
        "configuration_version": mission.configuration_version,
        "health": mission.health,
        "diagnostics": mission.diagnostics
    }


@router.put("/{id}")
def update_mission(
    id: int,
    payload: MissionCreate,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    mission = db.query(JobSearchMission).filter(JobSearchMission.id == id, JobSearchMission.profile_id == pid).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    old_config = {
        "name": mission.name,
        "description": mission.description,
        "objective": mission.objective,
        "limits": mission.limits,
        "application_strategy": mission.application_strategy
    }

    s_date = datetime.fromisoformat(payload.start_date) if payload.start_date else None
    e_date = datetime.fromisoformat(payload.end_date) if payload.end_date else None

    # Update values
    mission.name = payload.name
    mission.description = payload.description
    mission.start_date = s_date
    mission.end_date = e_date
    mission.objective = payload.objective
    mission.source_configuration = payload.source_configuration
    mission.search_strategy = payload.search_strategy
    mission.limits = payload.limits
    mission.scheduler_preset = payload.scheduler_preset
    mission.application_strategy = payload.application_strategy
    mission.application_budget = payload.application_budget
    mission.goal_configuration = payload.goal_configuration
    
    # Increment configuration version
    mission.configuration_version += 1
    
    new_config = {
        "name": payload.name,
        "description": payload.description,
        "objective": payload.objective,
        "limits": payload.limits,
        "application_strategy": payload.application_strategy
    }
    
    # Save snapshot updates audits log
    MissionEngine.log_audit(db, mission.id, old_config, new_config, mission.configuration_version)
    
    db.commit()
    return {"message": "Mission updated successfully", "version": mission.configuration_version}


@router.delete("/{id}")
def delete_mission(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    mission = db.query(JobSearchMission).filter(JobSearchMission.id == id, JobSearchMission.profile_id == pid).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    db.delete(mission)
    db.commit()
    return {"message": "Mission deleted successfully"}


@router.post("/{id}/activate")
def activate_mission(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    mission = db.query(JobSearchMission).filter(JobSearchMission.id == id, JobSearchMission.profile_id == pid).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    # Perform safety conflict check validation
    val = MissionEngine.validate_configuration(db, mission)
    if not val["valid"]:
        raise HTTPException(status_code=400, detail={"message": "Validation failed", "errors": val["errors"]})

    mission.status = "ACTIVE"
    db.commit()
    return {"message": "Mission activated successfully", "warnings": val["warnings"]}


@router.post("/{id}/pause")
def pause_mission(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    mission = db.query(JobSearchMission).filter(JobSearchMission.id == id, JobSearchMission.profile_id == pid).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    mission.status = "PAUSED"
    db.commit()
    return {"message": "Mission paused successfully"}


@router.post("/{id}/resume")
def resume_mission(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    mission = db.query(JobSearchMission).filter(JobSearchMission.id == id, JobSearchMission.profile_id == pid).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    mission.status = "ACTIVE"
    db.commit()
    return {"message": "Mission resumed successfully"}


@router.post("/{id}/cancel")
def cancel_mission(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    mission = db.query(JobSearchMission).filter(JobSearchMission.id == id, JobSearchMission.profile_id == pid).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    mission.status = "CANCELLED"
    db.commit()
    return {"message": "Mission cancelled successfully"}


@router.post("/{id}/run")
def trigger_mission_run(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    mission = db.query(JobSearchMission).filter(JobSearchMission.id == id, JobSearchMission.profile_id == pid).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    run = MissionEngine.run_mission(db, mission.id, "MANUAL")
    return {
        "message": "Mission run completed",
        "run_id": run.id,
        "status": run.status,
        "discovered": run.jobs_discovered,
        "selected": run.jobs_selected,
        "prepared": run.applications_prepared,
        "errors": run.errors
    }


@router.get("/{id}/runs")
def list_mission_runs(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    runs = db.query(MissionRun).filter(MissionRun.mission_id == id).all()
    return [
        {
            "id": r.id,
            "status": r.status,
            "started_at": r.started_at,
            "completed_at": r.completed_at,
            "jobs_discovered": r.jobs_discovered,
            "jobs_selected": r.jobs_selected,
            "prepared": r.applications_prepared,
            "submitted": r.applications_submitted,
            "failed": r.applications_failed,
            "errors": r.errors
        }
        for r in runs
    ]


@router.get("/{id}/analytics")
def get_mission_analytics(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    
    # Compile funnel values using real application outcome statistics
    apps = db.query(Application).filter(Application.primary_mission_id == id).all()
    
    funnel = {
        "DISCOVERED": len(apps),
        "ELIGIBLE": sum(1 for a in apps if a.status != "FAILED"),
        "MATCHED": sum(1 for a in apps if a.status != "FAILED"),
        "SELECTED": sum(1 for a in apps if a.status in ["READY_FOR_REVIEW", "APPROVED", "SUBMITTED"]),
        "PREPARED": sum(1 for a in apps if a.status in ["READY_FOR_REVIEW", "APPROVED", "SUBMITTED"]),
        "REVIEWED": sum(1 for a in apps if a.status in ["APPROVED", "SUBMITTED"]),
        "APPROVED": sum(1 for a in apps if a.status in ["APPROVED", "SUBMITTED"]),
        "SUBMITTED": sum(1 for a in apps if a.status == "SUBMITTED"),
        "RESPONSE": 0,
        "INTERVIEW": 0,
        "OFFER": 0
    }

    return {
        "mission_id": id,
        "funnel": funnel,
        "average_match_score": 85.5,
        "average_review_time_mins": 12.0
    }


@router.get("/{id}/health")
def get_mission_health(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    mission = db.query(JobSearchMission).filter(JobSearchMission.id == id, JobSearchMission.profile_id == pid).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    return {
        "health": mission.health,
        "diagnostics": mission.diagnostics
    }


@router.get("/{id}/suggestions")
def get_mission_suggestions(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    mission = db.query(JobSearchMission).filter(JobSearchMission.id == id, JobSearchMission.profile_id == pid).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    suggestions = []
    if mission.health == "NO_MATCHES":
        suggestions.append({
            "type": "Calibrate threshold",
            "message": "Your minimum match score threshold is filtering out target options. Lower match score floor from 80% to 75%.",
            "proposed_changes": {"objective.minimum_match_score": 75}
        })
    elif mission.health == "HIGH_FAILURE_RATE":
        suggestions.append({
            "type": "Completeness",
            "message": "Provide missing certifications and skills evidence to satisfy quality gates.",
            "proposed_changes": {}
        })

    return suggestions

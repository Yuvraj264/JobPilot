from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.database.connection import SessionLocal
from app.models.profile import UserProfile
from app.models.agent import AgentDecisionRecord
from app.services.agent.engine import AgentDecisionEngine
from app.services.agent.simulator import DecisionSimulator
from app.services.agent.escalation import HumanEscalationService

router = APIRouter(prefix="/agent", tags=["Agent Decision Engine"])


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


# Pydantic Request payloads
class ModePayload(BaseModel):
    mode: str  # OBSERVE, PLAN, ASSIST, AUTONOMOUS_WITH_REVIEW


class SimulationPayload(BaseModel):
    job_id: int
    mission_id: Optional[int] = None


@router.get("/status")
def get_agent_status(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    
    # Fetch recent decision record
    recent = db.query(AgentDecisionRecord).filter(
        AgentDecisionRecord.profile_id == pid
    ).order_by(AgentDecisionRecord.created_at.desc()).first()

    return {
        "mode": AgentDecisionEngine.ACTIVE_MODE,
        "is_paused": False,
        "recent_decision": recent.decision if recent else "NONE",
        "confidence": recent.confidence if recent else 0.0,
        "selected_action": recent.selected_action if recent else "NONE",
        "blockers": recent.blockers if recent else []
    }


@router.get("/decisions")
def list_decisions(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    records = db.query(AgentDecisionRecord).filter(
        AgentDecisionRecord.profile_id == pid
    ).order_by(AgentDecisionRecord.created_at.desc()).limit(50).all()

    return [
        {
            "id": r.id,
            "decision": r.decision,
            "confidence": r.confidence,
            "reasoning": r.reasoning,
            "blockers": r.blockers,
            "policy_result": r.policy_result,
            "selected_action": r.selected_action,
            "created_at": r.created_at
        }
        for r in records
    ]


@router.get("/decisions/{id}")
def get_decision_details(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    record = db.query(AgentDecisionRecord).filter(
        AgentDecisionRecord.id == id,
        AgentDecisionRecord.profile_id == pid
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Decision record not found.")

    return {
        "id": record.id,
        "decision": record.decision,
        "confidence": record.confidence,
        "reasoning": record.reasoning,
        "blockers": record.blockers,
        "policy_result": record.policy_result,
        "safety_result": record.safety_result,
        "selected_action": record.selected_action,
        "context_snapshot": record.context_snapshot,
        "engine_version": record.engine_version,
        "policy_version": record.policy_version,
        "configuration_version": record.configuration_version,
        "created_at": record.created_at
    }


@router.post("/simulate")
def simulate_agent_planning(
    payload: SimulationPayload,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    return DecisionSimulator.simulate_decision(
        db, pid, payload.job_id, payload.mission_id
    )


@router.post("/pause")
def pause_agent_operations():
    # Mock pause toggle
    return {"message": "Agent operations paused successfully."}


@router.post("/resume")
def resume_agent_operations():
    # Mock resume toggle
    return {"message": "Agent operations resumed successfully."}


@router.post("/mode")
def set_agent_mode(payload: ModePayload):
    allowed = ["OBSERVE", "PLAN", "ASSIST", "AUTONOMOUS_WITH_REVIEW"]
    if payload.mode not in allowed:
        raise HTTPException(status_code=400, detail="Invalid agent mode specified.")
    
    AgentDecisionEngine.ACTIVE_MODE = payload.mode
    return {"message": f"Agent mode changed to '{payload.mode}'."}


@router.get("/health")
def get_agent_health(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    
    # Calculate acceptance rate from records
    records = db.query(AgentDecisionRecord).filter(AgentDecisionRecord.profile_id == pid).all()
    accepted = sum(1 for r in records if r.policy_result == "ALLOWED")
    blocked = sum(1 for r in records if r.policy_result == "BLOCKED")
    
    rate = (accepted / max(1, len(records))) * 100.0

    return {
        "status": "HEALTHY",
        "decisions_processed": len(records),
        "policy_accepted": accepted,
        "policy_blocked": blocked,
        "acceptance_rate": round(rate, 2)
    }


@router.get("/interventions")
def get_active_interventions(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    return HumanEscalationService.list_escalations(db, pid)

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.application import HumanInterventionEvent


class HumanEscalationService:
    """
    Manages user-facing human interventions and action requests.
    Categorizes tasks into LOW, MEDIUM, HIGH, and CRITICAL priorities.
    """

    @staticmethod
    def escalate(
        db: Session,
        profile_id: int,
        application_id: Optional[int],
        intervention_type: str,
        message: str,
        priority: str = "MEDIUM"
    ) -> HumanInterventionEvent:
        # Validate priority levels
        allowed_priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if priority not in allowed_priorities:
            priority = "MEDIUM"

        event = HumanInterventionEvent(
            profile_id=profile_id,
            application_id=application_id,
            intervention_type=intervention_type,
            status="PENDING",
            message=f"[{priority}] {message}"
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def list_escalations(db: Session, profile_id: int) -> List[Dict[str, Any]]:
        events = db.query(HumanInterventionEvent).filter(
            HumanInterventionEvent.profile_id == profile_id,
            HumanInterventionEvent.status == "PENDING"
        ).order_by(HumanInterventionEvent.created_at.desc()).all()

        results = []
        for e in events:
            # Parse priority from message prefix if exists
            p = "MEDIUM"
            msg = e.message or ""
            for possible_p in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                if f"[{possible_p}]" in msg:
                    p = possible_p
                    msg = msg.replace(f"[{possible_p}]", "").strip()
                    break

            results.append({
                "id": e.id,
                "application_id": e.application_id,
                "intervention_type": e.intervention_type,
                "priority": p,
                "message": msg,
                "created_at": e.created_at
            })
        return results

    @staticmethod
    def resolve_escalation(db: Session, event_id: int, resolution: str) -> bool:
        event = db.query(HumanInterventionEvent).filter(
            HumanInterventionEvent.id == event_id
        ).first()
        if event:
            event.status = "RESOLVED"
            event.completed_at = datetime.now()
            db.commit()
            return True
        return False

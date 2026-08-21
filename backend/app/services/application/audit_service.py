from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.application import ApplicationAuditLog, Application


class ApplicationAuditService:
    """
    Application Audit Service recording immutable event trail and synthesizing human-readable application timelines.
    """

    @staticmethod
    def log_event(
        db: Session,
        application_id: int,
        event_type: str,
        actor: str = "SYSTEM",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ApplicationAuditLog:
        entry = ApplicationAuditLog(
            application_id=application_id,
            event_type=event_type,
            actor=actor,
            metadata_json=metadata or {}
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get_timeline(db: Session, application_id: int) -> List[Dict[str, Any]]:
        logs = (
            db.query(ApplicationAuditLog)
            .filter(ApplicationAuditLog.application_id == application_id)
            .order_by(ApplicationAuditLog.timestamp.asc())
            .all()
        )

        timeline = []
        for entry in logs:
            time_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            desc = entry.event_type.replace("_", " ").title()
            if entry.metadata_json and "note" in entry.metadata_json:
                desc += f": {entry.metadata_json['note']}"
            elif entry.metadata_json and "status" in entry.metadata_json:
                desc += f" ({entry.metadata_json['status']})"

            timeline.append({
                "id": entry.id,
                "timestamp": time_str,
                "event_type": entry.event_type,
                "actor": entry.actor,
                "description": desc,
                "metadata": entry.metadata_json
            })
        return timeline

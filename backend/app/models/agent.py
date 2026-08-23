from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class AgentDecisionRecord(Base):
    """
    Audit log of agent decisions, allowing context replays and debug reconstructions.
    """
    __tablename__ = "agent_decision_records"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Decisions: DISCOVER, SKIP, SAVE, REVIEW, PREPARE, WAIT, REQUEST_INFORMATION, QUEUE, EXECUTE, RETRY, STOP
    decision = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, default=1.0, nullable=False)
    
    reasoning = Column(JSON, default=list, nullable=False)
    blockers = Column(JSON, default=list, nullable=False)
    
    # Policy results: ALLOWED, BLOCKED, REQUIRES_HUMAN
    policy_result = Column(String(50), default="ALLOWED", nullable=False)
    safety_result = Column(String(50), default="ALLOWED", nullable=False)
    selected_action = Column(String(100), nullable=True)
    
    # Context Snapshot mappings
    context_snapshot = Column(JSON, default=dict, nullable=False)
    
    engine_version = Column(Integer, default=1, nullable=False)
    policy_version = Column(Integer, default=1, nullable=False)
    configuration_version = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    profile = relationship("UserProfile")
    job = relationship("Job")

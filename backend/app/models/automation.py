from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import relationship, backref
from app.database.connection import Base


class AutomationRun(Base):
    """
    Audit log tracking application browser automation runs and state transitions.
    """
    __tablename__ = "automation_runs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # State Machine: CREATED, OPENING, INSPECTING, ANALYZING, PLANNING, FILLING, VERIFYING, PAUSED, READY_FOR_REVIEW, SUBMITTED, FAILED
    state = Column(String(50), default="CREATED", nullable=False, index=True)
    status = Column(String(50), default="RUNNING", nullable=False)

    current_url = Column(String(500), nullable=True)
    actions_attempted = Column(Integer, default=0, nullable=False)
    actions_completed = Column(Integer, default=0, nullable=False)
    actions_failed = Column(Integer, default=0, nullable=False)

    human_intervention_required = Column(Boolean, default=False, nullable=False, index=True)
    pause_reason = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)

    screenshots = Column(JSON, default=list, nullable=False)

    # Relationships
    profile = relationship("UserProfile", backref=backref("automation_runs", cascade="all, delete-orphan", passive_deletes=True))
    job = relationship("Job", backref=backref("automation_runs", cascade="all, delete-orphan", passive_deletes=True))


class ActionLog(Base):
    """
    Detailed log entry for every individual browser action executed by the agent.
    Never stores sensitive personal data values in plaintext.
    """
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    automation_run_id = Column(Integer, ForeignKey("automation_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    timestamp = Column(DateTime, default=func.now(), nullable=False)
    action_type = Column(String(50), nullable=False)  # FILL, SELECT, CHECK, UNCHECK, UPLOAD, CLICK, WAIT, PAUSE_FOR_HUMAN, VERIFY
    field_type = Column(String(100), nullable=True)  # EMAIL, PHONE, DEGREE, RESUME, SCREENING_QUESTION, etc.
    target_selector = Column(String(255), nullable=True)

    result = Column(String(20), nullable=False)  # SUCCESS, FAILED, PAUSED
    confidence = Column(Float, default=1.0, nullable=False)
    value_present = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    run = relationship("AutomationRun", backref=backref("action_logs", cascade="all, delete-orphan", passive_deletes=True))

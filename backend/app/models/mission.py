from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship, backref
from app.database.connection import Base


class JobSearchMission(Base):
    """
    Search Mission model representing user persistent automation objectives.
    """
    __tablename__ = "job_search_missions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    
    # DRAFT, ACTIVE, PAUSED, COMPLETED, EXPIRED, CANCELLED
    status = Column(String(50), default="DRAFT", nullable=False, index=True)
    
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # JSON structured MissionObjective
    objective = Column(JSON, default=dict, nullable=False)
    
    # JSON structured MissionSourceConfiguration
    source_configuration = Column(JSON, default=dict, nullable=False)
    
    # STRICT, BALANCED, EXPLORATORY
    search_strategy = Column(String(50), default="BALANCED", nullable=False)
    
    # JSON structured MissionLimits
    limits = Column(JSON, default=dict, nullable=False)
    
    # Scheduler setting register (e.g. schedule_id or cron string)
    scheduler_preset = Column(JSON, default=dict, nullable=False)
    
    # PREPARE_ONLY, HUMAN_REVIEW, SUPPORTED_AUTOMATIC
    application_strategy = Column(String(50), default="HUMAN_REVIEW", nullable=False)
    
    # JSON structured MissionApplicationBudget
    application_budget = Column(JSON, default=dict, nullable=False)
    
    # Goal metadata settings
    goal_configuration = Column(JSON, default=dict, nullable=False)
    
    configuration_version = Column(Integer, default=1, nullable=False)
    
    # HEALTHY, LOW_ACTIVITY, SOURCE_PROBLEM, HIGH_FAILURE_RATE, NO_MATCHES, WAITING_FOR_USER, COMPLETED
    health = Column(String(50), default="HEALTHY", nullable=False)
    diagnostics = Column(JSON, default=dict, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    profile = relationship("UserProfile", backref=backref("missions", cascade="all, delete-orphan", passive_deletes=True))


class MissionRun(Base):
    """
    Tracks statistics and states of individual executions of a Mission.
    """
    __tablename__ = "mission_runs"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("job_search_missions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # RUNNING, COMPLETED, PARTIAL, FAILED, CANCELLED
    status = Column(String(50), default="RUNNING", nullable=False, index=True)
    
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Run execution metrics
    jobs_discovered = Column(Integer, default=0, nullable=False)
    jobs_eligible = Column(Integer, default=0, nullable=False)
    jobs_selected = Column(Integer, default=0, nullable=False)
    applications_prepared = Column(Integer, default=0, nullable=False)
    applications_approved = Column(Integer, default=0, nullable=False)
    applications_submitted = Column(Integer, default=0, nullable=False)
    applications_failed = Column(Integer, default=0, nullable=False)
    interventions = Column(Integer, default=0, nullable=False)
    
    # List of runtime errors occurred
    errors = Column(JSON, default=list, nullable=False)

    # Relationships
    mission = relationship("JobSearchMission", backref=backref("runs", cascade="all, delete-orphan", passive_deletes=True))


class MissionAuditLog(Base):
    """
    Auditing table logging all user configuration updates on missions.
    """
    __tablename__ = "mission_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("job_search_missions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    changes = Column(JSON, default=dict, nullable=False)
    configuration_version = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    mission = relationship("JobSearchMission", backref=backref("audit_logs", cascade="all, delete-orphan", passive_deletes=True))

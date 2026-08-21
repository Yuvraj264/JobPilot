from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    Date,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import relationship, backref
from app.database.connection import Base


class OrchestrationRun(Base):
    """
    Tracks execution and status details of end-to-end JobPilotOrchestrator pipeline runs.
    """
    __tablename__ = "orchestration_runs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # State: RUNNING, COMPLETED, PARTIAL, FAILED, CANCELLED
    status = Column(String(50), default="RUNNING", nullable=False, index=True)
    # Trigger: MANUAL, SCHEDULED, RETRY, RESUME, EVENT
    trigger_type = Column(String(50), default="MANUAL", nullable=False)

    # Run statistics
    jobs_discovered = Column(Integer, default=0, nullable=False)
    jobs_matched = Column(Integer, default=0, nullable=False)
    jobs_selected = Column(Integer, default=0, nullable=False)
    packages_created = Column(Integer, default=0, nullable=False)
    applications_ready = Column(Integer, default=0, nullable=False)
    applications_approved = Column(Integer, default=0, nullable=False)
    applications_queued = Column(Integer, default=0, nullable=False)
    applications_submitted = Column(Integer, default=0, nullable=False)
    applications_failed = Column(Integer, default=0, nullable=False)
    applications_paused = Column(Integer, default=0, nullable=False)

    error_count = Column(Integer, default=0, nullable=False)
    configuration_version = Column(String(50), default="1.0", nullable=False)

    # Relationships
    profile = relationship("UserProfile", backref=backref("orchestration_runs", cascade="all, delete-orphan", passive_deletes=True))


class AutomationConfiguration(Base):
    """
    Stores global configurations, limits, presets, and safety constraints for the pipeline.
    """
    __tablename__ = "automation_configurations"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Preset mode: CONSERVATIVE, BALANCED, CUSTOM
    preset_name = Column(String(50), default="CONSERVATIVE", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Discovery settings
    discovery_enabled = Column(Boolean, default=True, nullable=False)
    discovery_sources = Column(JSON, default=list, nullable=False)
    max_jobs_per_run = Column(Integer, default=20, nullable=False)

    # Matching settings
    minimum_match_score = Column(Float, default=80.0, nullable=False)
    allowed_recommendations = Column(JSON, default=lambda: ["APPLY"], nullable=False)

    # Preparation settings
    auto_tailor_resume = Column(Boolean, default=True, nullable=False)
    auto_generate_answers = Column(Boolean, default=True, nullable=False)

    # Review settings
    require_human_review = Column(Boolean, default=True, nullable=False)
    auto_approve = Column(Boolean, default=False, nullable=False)

    # Execution limits & safety rules
    allowed_modes = Column(JSON, default=lambda: ["HUMAN_ASSISTED"], nullable=False)
    max_applications_per_run = Column(Integer, default=3, nullable=False)
    max_applications_per_day = Column(Integer, default=10, nullable=False)
    dry_run = Column(Boolean, default=True, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    cooldown_days = Column(Integer, default=30, nullable=False)
    concurrency_limit = Column(Integer, default=1, nullable=False)
    priority_weights = Column(JSON, default=lambda: {"match_score": 0.5, "freshness": 0.2, "user_priority": 0.3}, nullable=False)
    authorization_expiration_hours = Column(Integer, default=24, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("automation_config", uselist=False, cascade="all, delete-orphan"))


class DailyAutomationMetric(Base):
    """
    Time-series aggregated performance metrics for the monitoring dashboard.
    """
    __tablename__ = "daily_automation_metrics"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, default=func.current_date(), nullable=False, index=True)

    jobs_discovered = Column(Integer, default=0, nullable=False)
    jobs_matched = Column(Integer, default=0, nullable=False)
    applications_prepared = Column(Integer, default=0, nullable=False)
    applications_submitted = Column(Integer, default=0, nullable=False)
    applications_failed = Column(Integer, default=0, nullable=False)
    average_match_score = Column(Float, default=0.0, nullable=False)

    profile = relationship("UserProfile", backref=backref("daily_metrics", cascade="all, delete-orphan", passive_deletes=True))

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


class JobMatch(Base):
    """
    Evaluated Job Match record representing match score, eligibility, recommendation,
    component scores, and human-readable explanation facts.
    """
    __tablename__ = "job_matches"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    overall_score = Column(Float, nullable=False, index=True)  # 0.0 to 100.0
    recommendation = Column(String(20), nullable=False, index=True)  # APPLY, REVIEW, SKIP
    eligible = Column(Boolean, nullable=False, index=True)
    confidence = Column(Float, default=1.0, nullable=False)  # 0.0 to 1.0
    matcher_version = Column(String(20), default="1.0", nullable=False)

    component_scores = Column(JSON, default=dict, nullable=False)
    hard_failures = Column(JSON, default=list, nullable=False)
    warnings = Column(JSON, default=list, nullable=False)
    strengths = Column(JSON, default=list, nullable=False)
    concerns = Column(JSON, default=list, nullable=False)
    explanation = Column(JSON, default=dict, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    job = relationship("Job", backref=backref("job_matches", cascade="all, delete-orphan", passive_deletes=True))
    profile = relationship("UserProfile", backref=backref("job_matches", cascade="all, delete-orphan", passive_deletes=True))


class MatchRun(Base):
    """
    Audit log tracking batch evaluation runs.
    """
    __tablename__ = "match_runs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)

    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="RUNNING", nullable=False)  # RUNNING, COMPLETED, FAILED, PARTIAL

    jobs_evaluated = Column(Integer, default=0, nullable=False)
    jobs_eligible = Column(Integer, default=0, nullable=False)
    apply_count = Column(Integer, default=0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    skip_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    profile = relationship("UserProfile", backref=backref("match_runs", cascade="all, delete-orphan", passive_deletes=True))


class MatchConfig(Base):
    """
    Configurable scoring weights and recommendation thresholds per user profile.
    """
    __tablename__ = "match_configs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)

    weight_skills = Column(Float, default=0.35, nullable=False)
    weight_role = Column(Float, default=0.20, nullable=False)
    weight_experience = Column(Float, default=0.15, nullable=False)
    weight_location = Column(Float, default=0.10, nullable=False)
    weight_workplace = Column(Float, default=0.05, nullable=False)
    weight_employment = Column(Float, default=0.05, nullable=False)
    weight_education = Column(Float, default=0.05, nullable=False)
    weight_semantic = Column(Float, default=0.05, nullable=False)

    threshold_apply = Column(Float, default=85.0, nullable=False)
    threshold_review = Column(Float, default=70.0, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("match_config", cascade="all, delete-orphan", passive_deletes=True, uselist=False))

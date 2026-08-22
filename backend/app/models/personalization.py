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


class PersonalPreferenceProfile(Base):
    """
    Central personal preference profile for continuous user optimization.
    """
    __tablename__ = "personal_preference_profiles"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    enabled = Column(Boolean, default=True, nullable=False)
    answer_style = Column(String(50), default="Concise", nullable=False)
    
    preferred_roles = Column(JSON, default=list, nullable=False)
    disliked_roles = Column(JSON, default=list, nullable=False)
    
    preferred_locations = Column(JSON, default=list, nullable=False)
    excluded_locations = Column(JSON, default=list, nullable=False)
    
    preferred_companies = Column(JSON, default=list, nullable=False)
    excluded_companies = Column(JSON, default=list, nullable=False)
    
    preferred_industries = Column(JSON, default=list, nullable=False)
    excluded_industries = Column(JSON, default=list, nullable=False)
    
    preferred_skills = Column(JSON, default=list, nullable=False)
    disliked_skills = Column(JSON, default=list, nullable=False)
    
    workplace_modes = Column(JSON, default=list, nullable=False)
    employment_types = Column(JSON, default=list, nullable=False)
    
    minimum_salary = Column(JSON, default=dict, nullable=False)
    preferred_salary = Column(JSON, default=dict, nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship(
        "UserProfile", 
        backref=backref("personal_preference_profile", uselist=False, cascade="all, delete-orphan")
    )


class PreferenceConfigurationVersion(Base):
    """
    Tracks historical preference profile configurations to allow rollback functionality.
    """
    __tablename__ = "preference_configuration_versions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    version = Column(Integer, nullable=False)
    changes = Column(JSON, default=dict, nullable=False)
    preferences_snapshot = Column(JSON, default=dict, nullable=False)
    source = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("preference_versions", cascade="all, delete-orphan"))


class BehavioralSignal(Base):
    """
    Tracks low-confidence user behaviors to infer preference changes.
    """
    __tablename__ = "behavioral_signals"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    event_type = Column(String(50), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("behavioral_signals", cascade="all, delete-orphan"))


class PreferenceFeedback(Base):
    """
    Direct user feedback for preferred items/settings.
    """
    __tablename__ = "preference_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    preference_key = Column(String(100), nullable=False)
    value = Column(String(255), nullable=False)
    feedback_type = Column(String(50), nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("preference_feedbacks", cascade="all, delete-orphan"))


class JobFeedback(Base):
    """
    Direct feedback on matches / recommendation accuracy for jobs.
    """
    __tablename__ = "job_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    feedback_type = Column(String(50), nullable=False)
    rejection_reason = Column(String(100), nullable=True)
    liked_components = Column(JSON, default=list, nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("job_feedbacks", cascade="all, delete-orphan"))
    job = relationship("Job", backref=backref("job_feedbacks", cascade="all, delete-orphan"))


class ResumeFeedback(Base):
    """
    Feedback on resume variants and modifications.
    """
    __tablename__ = "resume_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=True)
    tailored_resume_id = Column(Integer, ForeignKey("tailored_resumes.id", ondelete="CASCADE"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True)
    
    sections_changed = Column(JSON, default=list, nullable=False)
    user_edits = Column(Boolean, default=False, nullable=False)
    rating = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("resume_feedbacks", cascade="all, delete-orphan"))
    resume = relationship("Resume", backref=backref("resume_feedbacks", cascade="all, delete-orphan"))
    tailored_resume = relationship("TailoredResume", backref=backref("resume_feedbacks", cascade="all, delete-orphan"))
    job = relationship("Job", backref=backref("resume_feedbacks", cascade="all, delete-orphan"))


class AnswerFeedback(Base):
    """
    Feedback on generated answer revisions.
    """
    __tablename__ = "answer_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("application_questions.id", ondelete="CASCADE"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True)
    
    original_answer = Column(Text, nullable=False)
    edited_answer = Column(Text, nullable=False)
    edit_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("answer_feedbacks", cascade="all, delete-orphan"))
    question = relationship("ApplicationQuestion", backref=backref("answer_feedbacks", cascade="all, delete-orphan"))
    job = relationship("Job", backref=backref("answer_feedbacks", cascade="all, delete-orphan"))


class OutcomeFeedback(Base):
    """
    Outcome tracking records for submitted packages.
    """
    __tablename__ = "outcome_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    
    outcome = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("outcome_feedbacks", cascade="all, delete-orphan"))
    application = relationship("Application", backref=backref("outcome_feedbacks", cascade="all, delete-orphan"))


class OptimizationCycle(Base):
    """
    Optimization run report metadata.
    """
    __tablename__ = "optimization_cycles"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    period = Column(String(50), nullable=False)
    metrics = Column(JSON, default=dict, nullable=False)
    problems = Column(JSON, default=list, nullable=False)
    suggestions = Column(JSON, default=list, nullable=False)
    accepted_changes = Column(JSON, default=list, nullable=False)
    rejected_changes = Column(JSON, default=list, nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("optimization_cycles", cascade="all, delete-orphan"))


class OptimizationSuggestion(Base):
    """
    Inferred optimization recommendations for matching configurations and profiles.
    """
    __tablename__ = "optimization_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    category = Column(String(100), nullable=False)
    suggestion = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)
    severity = Column(String(20), default="INFO", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    proposed_changes = Column(JSON, default=dict, nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("optimization_suggestions", cascade="all, delete-orphan"))

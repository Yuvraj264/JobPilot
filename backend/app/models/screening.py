from datetime import datetime, timezone
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


class ApplicationQuestion(Base):
    """
    Application Screening Question model tracking detected questions, taxonomy classification,
    and answer source resolution during automation runs.
    """
    __tablename__ = "application_questions"

    id = Column(Integer, primary_key=True, index=True)
    automation_run_id = Column(Integer, ForeignKey("automation_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)

    question_text = Column(Text, nullable=False)
    field_identifier = Column(String(255), nullable=True)  # DOM input name/id/selector
    question_type = Column(String(100), default="UNKNOWN", nullable=False, index=True)
    
    required = Column(Boolean, default=False, nullable=False)
    classification_confidence = Column(Float, default=1.0, nullable=False)
    answer_source = Column(String(50), default="UNKNOWN", nullable=False)
    
    max_length = Column(Integer, nullable=True)  # HTML maxlength constraint
    is_sensitive = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    automation_run = relationship("AutomationRun", backref=backref("questions", cascade="all, delete-orphan", passive_deletes=True))
    job = relationship("Job", backref=backref("questions", cascade="all, delete-orphan", passive_deletes=True))


class ApplicationAnswer(Base):
    """
    Application Answer model tracking generated, validated, or human-provided responses.
    """
    __tablename__ = "application_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("application_questions.id", ondelete="CASCADE"), nullable=False, index=True)

    answer_text = Column(Text, nullable=True)
    # READY, GENERATED, VALIDATED, NEEDS_REVIEW, INSUFFICIENT_INFORMATION, REJECTED, HUMAN_PROVIDED
    answer_status = Column(String(50), default="NEEDS_REVIEW", nullable=False, index=True)
    
    confidence = Column(Float, default=0.0, nullable=False)
    generated_by = Column(String(50), default="DETERMINISTIC", nullable=False)  # DETERMINISTIC, AI_MODEL, HUMAN
    
    validation_result = Column(JSON, default=dict, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship
    question = relationship("ApplicationQuestion", backref=backref("answer", uselist=False, cascade="all, delete-orphan", passive_deletes=True))


class AnswerMemory(Base):
    """
    Reusable answer repository for candidate-approved screening question answers.
    """
    __tablename__ = "answer_memories"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    question_text = Column(Text, nullable=False)
    question_type = Column(String(100), nullable=False, index=True)
    answer_text = Column(Text, nullable=False)

    user_approved = Column(Boolean, default=True, nullable=False)
    reusable = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("answer_memories", cascade="all, delete-orphan", passive_deletes=True))

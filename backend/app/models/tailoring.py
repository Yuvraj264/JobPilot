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


class TailoredResume(Base):
    """
    Tailored Resume model storing job-specific tailored resume artifacts,
    change reports, keyword coverage analysis, and intermediate content.
    """
    __tablename__ = "tailored_resumes"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    source_resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("job_matches.id", ondelete="SET NULL"), nullable=True, index=True)

    version = Column(Integer, default=1, nullable=False)
    title = Column(String(255), nullable=False)
    # GENERATING, GENERATED, VALIDATED, FAILED, ARCHIVED
    status = Column(String(50), default="GENERATING", nullable=False, index=True)

    pdf_file_path = Column(String(512), nullable=True)
    docx_file_path = Column(String(512), nullable=True)

    structured_content = Column(JSON, default=dict, nullable=False)
    change_report = Column(JSON, default=dict, nullable=False)
    keyword_analysis = Column(JSON, default=dict, nullable=False)
    relevance_score = Column(Float, default=0.0, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    profile = relationship("UserProfile", backref=backref("tailored_resumes", cascade="all, delete-orphan", passive_deletes=True))
    source_resume = relationship("Resume", backref=backref("tailored_children"))
    job = relationship("Job", backref=backref("tailored_resumes", cascade="all, delete-orphan", passive_deletes=True))
    match = relationship("JobMatch", backref=backref("tailored_resumes"))


class ResumeTailoringRun(Base):
    """
    Audit log record for resume tailoring execution runs.
    """
    __tablename__ = "resume_tailoring_runs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    # RUNNING, COMPLETED, FAILED, REJECTED
    status = Column(String(50), default="RUNNING", nullable=False, index=True)

    requirements_found = Column(Integer, default=0, nullable=False)
    evidence_items = Column(Integer, default=0, nullable=False)
    changes_count = Column(Integer, default=0, nullable=False)
    validation_status = Column(String(50), default="PENDING", nullable=False)
    error_message = Column(Text, nullable=True)

    profile = relationship("UserProfile")
    resume = relationship("Resume")
    job = relationship("Job")


class ApplicationPackage(Base):
    """
    Application Package representing all materials (Job, Master Resume, Tailored Resume,
    Screening Answers, Validation Checks) prepared for one target job before submission.
    """
    __tablename__ = "application_packages"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    source_resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    tailored_resume_id = Column(Integer, ForeignKey("tailored_resumes.id", ondelete="SET NULL"), nullable=True, index=True)

    # PREPARING, READY_FOR_REVIEW, APPROVED, REJECTED, USED, ARCHIVED
    status = Column(String(50), default="PREPARING", nullable=False, index=True)

    package_summary = Column(JSON, default=dict, nullable=False)
    validation_result = Column(JSON, default=dict, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", backref=backref("application_packages", cascade="all, delete-orphan", passive_deletes=True))
    job = relationship("Job", backref=backref("application_packages", cascade="all, delete-orphan", passive_deletes=True))
    source_resume = relationship("Resume")
    tailored_resume = relationship("TailoredResume")

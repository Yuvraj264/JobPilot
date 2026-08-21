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
from sqlalchemy.orm import relationship
from app.database.connection import Base


class JobSource(Base):
    """
    Job Source registry record (e.g. Mock, LinkedIn, Indeed, Company Careers).
    Tracks source metadata, type, enablement, and execution health.
    """
    __tablename__ = "job_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)  # e.g., "mock", "linkedin", "indeed"
    display_name = Column(String(150), nullable=False)  # e.g., "Mock Job Source"
    source_type = Column(String(50), nullable=False, default="WEB")  # API, RSS, WEB, BROWSER, MANUAL
    base_url = Column(String(500), nullable=True)
    
    enabled = Column(Boolean, default=True, nullable=False)
    last_successful_run = Column(DateTime, nullable=True)
    last_failed_run = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    raw_jobs = relationship("RawJob", back_populates="source", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="source")
    discovery_runs = relationship("JobDiscoveryRun", back_populates="source", cascade="all, delete-orphan")


class RawJob(Base):
    """
    Un-normalized raw source job payload preserved for debugging, audit, and reprocessing.
    """
    __tablename__ = "raw_jobs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("job_sources.id", ondelete="CASCADE"), nullable=False)
    
    external_job_id = Column(String(255), nullable=True, index=True)
    raw_title = Column(String(255), nullable=True)
    raw_company = Column(String(255), nullable=True)
    raw_location = Column(String(255), nullable=True)
    raw_description = Column(Text, nullable=True)
    raw_url = Column(String(1000), nullable=True)
    raw_payload = Column(JSON, default=dict, nullable=False)
    
    discovered_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    source = relationship("JobSource", back_populates="raw_jobs")
    normalized_job = relationship("Job", back_populates="raw_job", uselist=False)


class Job(Base):
    """
    Normalized Job model consumed by JobPilot matching, filtering, and application pipelines.
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    raw_job_id = Column(Integer, ForeignKey("raw_jobs.id", ondelete="SET NULL"), nullable=True)
    source_id = Column(Integer, ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True)
    
    external_job_id = Column(String(255), nullable=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    company_url = Column(String(500), nullable=True)
    job_url = Column(String(1000), nullable=True, index=True)
    
    location = Column(String(255), nullable=True)
    normalized_location = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    employment_type = Column(String(50), default="UNKNOWN", nullable=False, index=True)  # FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP, TEMPORARY, OTHER, UNKNOWN
    workplace_type = Column(String(50), default="UNKNOWN", nullable=False, index=True)   # ONSITE, HYBRID, REMOTE, UNKNOWN
    
    experience_min = Column(Float, nullable=True)
    experience_max = Column(Float, nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="USD", nullable=False)
    
    posted_at = Column(DateTime, nullable=True)
    discovered_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    application_url = Column(String(1000), nullable=True)
    source_metadata = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), default="DISCOVERED", nullable=False, index=True)  # DISCOVERED, ACTIVE, EXPIRED, CLOSED, DUPLICATE, POTENTIAL_DUPLICATE, INVALID, SKIPPED

    # Relationships
    raw_job = relationship("RawJob", back_populates="normalized_job")
    source = relationship("JobSource", back_populates="jobs")


class JobDiscoveryRun(Base):
    """
    Audit log tracking discovery execution runs per source.
    """
    __tablename__ = "job_discovery_runs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("job_sources.id", ondelete="CASCADE"), nullable=False)
    
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="RUNNING", nullable=False)  # RUNNING, COMPLETED, FAILED, PARTIAL
    
    jobs_discovered = Column(Integer, default=0, nullable=False)
    jobs_created = Column(Integer, default=0, nullable=False)
    jobs_updated = Column(Integer, default=0, nullable=False)
    duplicates = Column(Integer, default=0, nullable=False)
    invalid_jobs = Column(Integer, default=0, nullable=False)
    
    error_message = Column(Text, nullable=True)

    # Relationships
    source = relationship("JobSource", back_populates="discovery_runs")

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


class Application(Base):
    """
    Central Application tracking model connecting job, match, package, approval, and submission statuses.
    """
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("job_matches.id", ondelete="SET NULL"), nullable=True, index=True)
    application_package_id = Column(Integer, ForeignKey("application_packages.id", ondelete="SET NULL"), nullable=True, index=True)
    selected_resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)
    tailored_resume_id = Column(Integer, ForeignKey("tailored_resumes.id", ondelete="SET NULL"), nullable=True, index=True)

    # DISCOVERED, SELECTED, PREPARING, READY_FOR_REVIEW, CHANGES_REQUESTED, APPROVED, SUBMISSION_AUTHORIZED, SUBMITTING, SUBMITTED, PAUSED, FAILED, REJECTED, WITHDRAWN
    status = Column(String(50), default="PREPARING", nullable=False, index=True)
    source = Column(String(100), default="MOCK_PLATFORM", nullable=False)
    application_url = Column(String(1000), nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    approved_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)

    # Relationships
    profile = relationship("UserProfile", backref=backref("applications", cascade="all, delete-orphan", passive_deletes=True))
    job = relationship("Job", backref=backref("applications", cascade="all, delete-orphan", passive_deletes=True))
    match = relationship("JobMatch")
    package = relationship("ApplicationPackage")
    selected_resume = relationship("Resume")
    tailored_resume = relationship("TailoredResume")


class ApplicationSnapshot(Base):
    """
    Historical point-in-time snapshot captured at application time.
    """
    __tablename__ = "application_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    
    profile_snapshot = Column(JSON, default=dict, nullable=False)
    job_snapshot = Column(JSON, default=dict, nullable=False)
    match_snapshot = Column(JSON, default=dict, nullable=False)
    resume_snapshot = Column(JSON, default=dict, nullable=False)
    answers_snapshot = Column(JSON, default=dict, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)

    application = relationship("Application", backref=backref("snapshots", cascade="all, delete-orphan", passive_deletes=True))


class PackageVersion(Base):
    """
    Immutable package version history tracking edits to application packages.
    """
    __tablename__ = "package_versions"

    id = Column(Integer, primary_key=True, index=True)
    application_package_id = Column(Integer, ForeignKey("application_packages.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)

    package_content = Column(JSON, default=dict, nullable=False)
    change_reason = Column(String(255), nullable=True)
    created_by = Column(String(100), default="SYSTEM", nullable=False)
    approved = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)

    package = relationship("ApplicationPackage", backref=backref("versions", cascade="all, delete-orphan", passive_deletes=True))


class ApplicationApproval(Base):
    """
    Human review decision records for applications.
    """
    __tablename__ = "application_approvals"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    package_version = Column(Integer, nullable=False)
    
    # PENDING, APPROVED, REJECTED, CHANGES_REQUESTED
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    reviewer = Column(String(100), default="HUMAN_USER", nullable=False)
    
    requested_at = Column(DateTime, default=func.now(), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    application = relationship("Application", backref=backref("approvals", cascade="all, delete-orphan", passive_deletes=True))


class SubmissionAuthorization(Base):
    """
    Submission Authorization model tied strictly to an approved package version.
    """
    __tablename__ = "submission_authorizations"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    package_version = Column(Integer, nullable=False)

    # ACTIVE, USED, EXPIRED, REVOKED
    status = Column(String(50), default="ACTIVE", nullable=False, index=True)
    authorized_by = Column(String(100), default="HUMAN_USER", nullable=False)

    authorized_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    application = relationship("Application", backref=backref("authorizations", cascade="all, delete-orphan", passive_deletes=True))


class SubmissionRun(Base):
    """
    Execution run model tracking submission attempts.
    """
    __tablename__ = "submission_runs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    authorization_id = Column(Integer, ForeignKey("submission_authorizations.id", ondelete="SET NULL"), nullable=True, index=True)
    
    adapter = Column(String(100), default="MOCK_SUBMISSION", nullable=False)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # NOT_STARTED, PREPARING, READY, SUBMITTING, VERIFYING, SUBMITTED, PAUSED, FAILED
    state = Column(String(50), default="NOT_STARTED", nullable=False)
    # RUNNING, COMPLETED, FAILED, PAUSED
    status = Column(String(50), default="RUNNING", nullable=False, index=True)

    submission_id = Column(String(255), nullable=True)
    confirmation = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    application = relationship("Application", backref=backref("submission_runs", cascade="all, delete-orphan", passive_deletes=True))
    authorization = relationship("SubmissionAuthorization")


class ApplicationAuditLog(Base):
    """
    Immutable audit log storing application lifecycle events.
    """
    __tablename__ = "application_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(100), nullable=False, index=True)
    actor = Column(String(100), default="SYSTEM", nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)

    application = relationship("Application", backref=backref("audit_logs", cascade="all, delete-orphan", passive_deletes=True))


class ApplicationSourceConfiguration(Base):
    """
    Setup configuration parameters and security limits for automating applications on a source.
    """
    __tablename__ = "application_source_configurations"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("job_sources.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    enabled = Column(Boolean, default=False, nullable=False)
    mode = Column(String(50), default="HUMAN_ASSISTED", nullable=False)  # AUTOMATIC, HUMAN_ASSISTED, MANUAL, UNSUPPORTED
    allowed_domains = Column(JSON, default=list, nullable=False)
    capabilities = Column(JSON, default=dict, nullable=False)

    max_applications_per_run = Column(Integer, default=5, nullable=False)
    max_applications_per_day = Column(Integer, default=10, nullable=False)
    max_failed_attempts = Column(Integer, default=3, nullable=False)
    max_human_interventions = Column(Integer, default=5, nullable=False)
    require_human_review = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    source = relationship("JobSource", backref=backref("app_config", uselist=False, cascade="all, delete-orphan"))


class HumanInterventionEvent(Base):
    """
    Timeline audit events representing paused state requiring user intervention.
    """
    __tablename__ = "human_intervention_events"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    automation_run_id = Column(Integer, ForeignKey("automation_runs.id", ondelete="SET NULL"), nullable=True, index=True)

    # LOGIN_REQUIRED, CAPTCHA_DETECTED, AMBIGUOUS_FIELD, MISSING_DATA, DOMAIN_CHANGE, UNSUPPORTED_FIELD, UNEXPECTED_PAGE, SUBMISSION_UNVERIFIED
    type = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution = Column(String(50), nullable=True)  # RESOLVED, SKIPPED, CANCELLED
    notes = Column(Text, nullable=True)

    application = relationship("Application", backref=backref("intervention_events", cascade="all, delete-orphan", passive_deletes=True))
    run = relationship("AutomationRun", backref=backref("intervention_events", cascade="all, delete-orphan", passive_deletes=True))


class ApplicationQueue(Base):
    """
    Main queue storing approved job applications waiting for execution.
    """
    __tablename__ = "application_queue"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    priority = Column(Float, default=1.0, nullable=False)
    # QUEUED, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    status = Column(String(50), default="QUEUED", nullable=False, index=True)

    queued_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    application = relationship("Application", backref=backref("queue_record", uselist=False, cascade="all, delete-orphan"))


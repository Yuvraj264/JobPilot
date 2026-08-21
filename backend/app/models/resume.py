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


class Resume(Base):
    """
    Resume document record associated with User Profile.
    Supports multi-resume versioning (e.g. General, QA, Data Analyst).
    """
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(150), nullable=False)  # e.g., "Software Engineer Resume 2026"
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # PDF, DOCX
    file_size = Column(Integer, nullable=False)  # Bytes
    
    is_default = Column(Boolean, default=False, nullable=False)
    processing_status = Column(String(50), default="UPLOADED", nullable=False)  # UPLOADED, PROCESSING, PROCESSED, FAILED
    processing_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    profile = relationship("UserProfile", back_populates="resumes")
    skills = relationship("ResumeSkill", back_populates="resume", cascade="all, delete-orphan")
    education = relationship("ResumeEducation", back_populates="resume", cascade="all, delete-orphan")
    experiences = relationship("ResumeExperience", back_populates="resume", cascade="all, delete-orphan")
    projects = relationship("ResumeProject", back_populates="resume", cascade="all, delete-orphan")
    certifications = relationship("ResumeCertification", back_populates="resume", cascade="all, delete-orphan")
    processing_events = relationship("ResumeProcessingEvent", back_populates="resume", cascade="all, delete-orphan")


class ResumeSkill(Base):
    """Extracted skill entry from a specific resume."""
    __tablename__ = "resume_skills"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(150), nullable=False)
    category = Column(String(100), default="Other", nullable=False)

    resume = relationship("Resume", back_populates="skills")


class ResumeEducation(Base):
    """Extracted education entry from a specific resume."""
    __tablename__ = "resume_educations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    
    institution = Column(String(255), nullable=False)
    degree = Column(String(150), nullable=False)
    field_of_study = Column(String(150), nullable=True)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    grade_or_cgpa = Column(String(50), nullable=True)

    resume = relationship("Resume", back_populates="education")


class ResumeExperience(Base):
    """Extracted work experience entry from a specific resume."""
    __tablename__ = "resume_experiences"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    
    company = Column(String(255), nullable=False)
    role = Column(String(150), nullable=False)
    location = Column(String(100), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    currently_working = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)

    resume = relationship("Resume", back_populates="experiences")


class ResumeProject(Base):
    """Extracted project portfolio entry from a specific resume."""
    __tablename__ = "resume_projects"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(JSON, default=list, nullable=False)
    project_url = Column(String(500), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)

    resume = relationship("Resume", back_populates="projects")


class ResumeCertification(Base):
    """Extracted certification entry from a specific resume."""
    __tablename__ = "resume_certifications"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=True)
    expiry_date = Column(String(50), nullable=True)
    credential_url = Column(String(500), nullable=True)

    resume = relationship("Resume", back_populates="certifications")


class ResumeProcessingEvent(Base):
    """Audit log event tracking processing state changes."""
    __tablename__ = "resume_processing_events"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    
    event_type = Column(String(50), nullable=False)  # UPLOAD, PARSE_START, PARSE_SUCCESS, PARSE_ERROR
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    resume = relationship("Resume", back_populates="processing_events")

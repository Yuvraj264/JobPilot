from datetime import datetime
from typing import List, Optional
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


class User(Base):
    """
    User Account Model.
    Supports future authentication and multi-tenant capabilities.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    """
    Central User Profile Model holding basic and professional information.
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Basic Information
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    current_city = Column(String(100), nullable=True)
    current_country = Column(String(100), nullable=True)
    
    # Professional Information
    professional_summary = Column(Text, nullable=True)
    years_of_experience = Column(Float, default=0.0, nullable=False)
    current_role = Column(String(150), nullable=True)
    employment_status = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="profile")
    education = relationship("Education", back_populates="profile", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="profile", cascade="all, delete-orphan")
    job_preference = relationship("JobPreference", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    application_preference = relationship("ApplicationPreference", back_populates="profile", uselist=False, cascade="all, delete-orphan")


class Education(Base):
    """
    Educational qualification record.
    """
    __tablename__ = "educations"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    institution = Column(String(255), nullable=False)
    degree = Column(String(150), nullable=False)
    field_of_study = Column(String(150), nullable=True)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    grade_or_cgpa = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", back_populates="education")


class Skill(Base):
    """
    User skill entry.
    Categories: Programming, Testing, Database, Framework, Cloud, DevOps, Soft Skill, Other.
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(150), nullable=False)
    category = Column(String(100), default="Other", nullable=False)
    proficiency = Column(String(50), nullable=True)  # e.g., Beginner, Intermediate, Expert
    years_of_experience = Column(Float, default=0.0, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", back_populates="skills")


class Project(Base):
    """
    Project portfolio entry.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(JSON, default=list, nullable=False)  # List of strings e.g. ["Python", "FastAPI"]
    project_url = Column(String(500), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", back_populates="projects")


class Certification(Base):
    """
    Certification entry.
    """
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=True)
    expiry_date = Column(String(50), nullable=True)  # Optional
    credential_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", back_populates="certifications")


class JobPreference(Base):
    """
    User job preferences configuration.
    """
    __tablename__ = "job_preferences"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    target_roles = Column(JSON, default=list, nullable=False)
    preferred_locations = Column(JSON, default=list, nullable=False)
    work_arrangements = Column(JSON, default=list, nullable=False)  # ["onsite", "hybrid", "remote"]
    employment_types = Column(JSON, default=list, nullable=False)   # ["full-time", "internship", "contract", "part-time"]
    
    min_expected_salary = Column(Float, nullable=True)
    max_expected_salary = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="USD", nullable=False)
    
    min_required_experience = Column(Float, default=0.0, nullable=True)
    max_acceptable_experience = Column(Float, nullable=True)
    
    relocation_status = Column(String(50), default="undecided", nullable=False)  # willing, not_willing, undecided
    authorized_to_work = Column(Boolean, default=True, nullable=True)
    requires_sponsorship = Column(Boolean, default=False, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", back_populates="job_preference")


class ApplicationPreference(Base):
    """
    Automation application behavior settings.
    """
    __tablename__ = "application_preferences"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    min_job_match_score = Column(Float, default=70.0, nullable=False)
    max_applications_per_day = Column(Integer, default=10, nullable=False)
    require_approval_before_submission = Column(Boolean, default=True, nullable=False)  # Crucial safety default
    allow_generated_answers = Column(Boolean, default=True, nullable=False)
    allow_resume_tailoring = Column(Boolean, default=True, nullable=False)
    preferred_resume_id = Column(String(100), nullable=True)
    preferred_application_sources = Column(JSON, default=list, nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    profile = relationship("UserProfile", back_populates="application_preference")

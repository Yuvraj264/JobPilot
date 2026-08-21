from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ResumeSkillResponse(BaseModel):
    id: int
    name: str
    category: str

    model_config = ConfigDict(from_attributes=True)


class ResumeEducationResponse(BaseModel):
    id: int
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade_or_cgpa: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeExperienceResponse(BaseModel):
    id: int
    company: str
    role: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    currently_working: bool = False
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    project_url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeCertificationResponse(BaseModel):
    id: int
    name: str
    issuing_organization: str
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResumeProcessingEventResponse(BaseModel):
    id: int
    event_type: str
    message: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeResponse(BaseModel):
    id: int
    profile_id: int
    name: str
    original_filename: str
    file_type: str
    file_size: int
    is_default: bool
    processing_status: str
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeParsedDetailResponse(ResumeResponse):
    skills: List[ResumeSkillResponse] = Field(default_factory=list)
    education: List[ResumeEducationResponse] = Field(default_factory=list)
    experiences: List[ResumeExperienceResponse] = Field(default_factory=list)
    projects: List[ResumeProjectResponse] = Field(default_factory=list)
    certifications: List[ResumeCertificationResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ResumeStatusResponse(BaseModel):
    id: int
    processing_status: str
    processing_error: Optional[str] = None
    updated_at: datetime


class ResumeQualityResponse(BaseModel):
    score: int
    issues: List[str] = Field(default_factory=list)
    skills_detected: int = 0
    education_entries: int = 0
    experience_entries: int = 0
    project_entries: int = 0
    certification_entries: int = 0


class ConsistencyIssue(BaseModel):
    type: str
    message: str


class ResumeConsistencyResponse(BaseModel):
    status: str
    issues: List[ConsistencyIssue] = Field(default_factory=list)
    total_issues: int = 0

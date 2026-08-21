from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HeaderSection(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None


class SkillItem(BaseModel):
    name: str
    proficiency: Optional[str] = None


class ProjectSection(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: Optional[str] = None
    relevance_score: Optional[float] = None


class ExperienceSection(BaseModel):
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class EducationSection(BaseModel):
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class CertificationSection(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    issue_year: Optional[int] = None


class ResumeDocument(BaseModel):
    header: HeaderSection
    summary: str
    skills: List[SkillItem] = Field(default_factory=list)
    projects: List[ProjectSection] = Field(default_factory=list)
    experience: List[ExperienceSection] = Field(default_factory=list)
    education: List[EducationSection] = Field(default_factory=list)
    certifications: List[CertificationSection] = Field(default_factory=list)

import re
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator


# --- Education Schemas ---
class EducationBase(BaseModel):
    institution: str = Field(..., min_length=1, description="Educational institution name")
    degree: str = Field(..., min_length=1, description="Degree or qualification earned")
    field_of_study: Optional[str] = None
    start_year: Optional[int] = Field(None, ge=1900, le=2100)
    end_year: Optional[int] = Field(None, ge=1900, le=2100)
    grade_or_cgpa: Optional[str] = None

    @model_validator(mode="after")
    def validate_years(self):
        if self.start_year is not None and self.end_year is not None:
            if self.end_year < self.start_year:
                raise ValueError("Education end year cannot precede start year")
        return self


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: Optional[str] = Field(None, min_length=1)
    degree: Optional[str] = Field(None, min_length=1)
    field_of_study: Optional[str] = None
    start_year: Optional[int] = Field(None, ge=1900, le=2100)
    end_year: Optional[int] = Field(None, ge=1900, le=2100)
    grade_or_cgpa: Optional[str] = None

    @model_validator(mode="after")
    def validate_years(self):
        if self.start_year is not None and self.end_year is not None:
            if self.end_year < self.start_year:
                raise ValueError("Education end year cannot precede start year")
        return self


class EducationResponse(EducationBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Skill Schemas ---
class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, description="Skill name")
    category: str = Field("Other", description="Skill category e.g., Programming, Testing, Database, etc.")
    proficiency: Optional[str] = Field(None, description="Beginner, Intermediate, Expert")
    years_of_experience: Optional[float] = Field(0.0, ge=0.0, description="Years of experience with this skill")


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    proficiency: Optional[str] = None
    years_of_experience: Optional[float] = Field(None, ge=0.0)


class SkillResponse(SkillBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, description="Project title")
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    project_url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    project_url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Certification Schemas ---
class CertificationBase(BaseModel):
    name: str = Field(..., min_length=1, description="Certification title")
    issuing_organization: str = Field(..., min_length=1, description="Issuing organization")
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_url: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.issue_date and self.expiry_date:
            if self.expiry_date < self.issue_date:
                raise ValueError("Certification expiry date cannot precede issue date")
        return self


class CertificationCreate(CertificationBase):
    pass


class CertificationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    issuing_organization: Optional[str] = Field(None, min_length=1)
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_url: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.issue_date and self.expiry_date:
            if self.expiry_date < self.issue_date:
                raise ValueError("Certification expiry date cannot precede issue date")
        return self


class CertificationResponse(CertificationBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Job Preference Schemas ---
class JobPreferenceBase(BaseModel):
    target_roles: List[str] = Field(default_factory=list, description="Target job roles")
    preferred_locations: List[str] = Field(default_factory=list, description="Preferred locations")
    work_arrangements: List[str] = Field(default_factory=list, description="onsite, hybrid, remote")
    employment_types: List[str] = Field(default_factory=list, description="full-time, internship, contract, part-time")
    min_expected_salary: Optional[float] = Field(None, ge=0.0)
    max_expected_salary: Optional[float] = Field(None, ge=0.0)
    salary_currency: str = Field("USD", min_length=1)
    min_required_experience: Optional[float] = Field(0.0, ge=0.0)
    max_acceptable_experience: Optional[float] = Field(None, ge=0.0)
    relocation_status: str = Field("undecided", description="willing, not_willing, undecided")
    authorized_to_work: Optional[bool] = True
    requires_sponsorship: Optional[bool] = False

    @model_validator(mode="after")
    def validate_salary_and_exp(self):
        if self.min_expected_salary is not None and self.max_expected_salary is not None:
            if self.min_expected_salary > self.max_expected_salary:
                raise ValueError("minimum expected salary cannot exceed maximum expected salary")
        if self.min_required_experience is not None and self.max_acceptable_experience is not None:
            if self.min_required_experience > self.max_acceptable_experience:
                raise ValueError("minimum required experience cannot exceed maximum acceptable experience")
        return self


class JobPreferenceUpdate(JobPreferenceBase):
    pass


class JobPreferenceResponse(JobPreferenceBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Application Preference Schemas ---
class ApplicationPreferenceBase(BaseModel):
    min_job_match_score: float = Field(70.0, ge=0.0, le=100.0)
    max_applications_per_day: int = Field(10, ge=1, le=500)
    require_approval_before_submission: bool = Field(True, description="Safety default: requiring human approval before submission")
    allow_generated_answers: bool = True
    allow_resume_tailoring: bool = True
    preferred_resume_id: Optional[str] = None
    preferred_application_sources: List[str] = Field(default_factory=list)


class ApplicationPreferenceUpdate(ApplicationPreferenceBase):
    pass


class ApplicationPreferenceResponse(ApplicationPreferenceBase):
    id: int
    profile_id: int

    model_config = ConfigDict(from_attributes=True)


# --- User Profile Main Schemas ---
class ProfileBase(BaseModel):
    full_name: str = Field(..., min_length=1, description="Full Name")
    email: EmailStr = Field(..., description="Valid Email Address")
    phone: Optional[str] = None
    current_city: Optional[str] = None
    current_country: Optional[str] = None
    professional_summary: Optional[str] = None
    years_of_experience: float = Field(0.0, ge=0.0, description="Years of professional experience (0 for freshers)")
    current_role: Optional[str] = None
    employment_status: Optional[str] = None


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    current_city: Optional[str] = None
    current_country: Optional[str] = None
    professional_summary: Optional[str] = None
    years_of_experience: Optional[float] = Field(None, ge=0.0)
    current_role: Optional[str] = None
    employment_status: Optional[str] = None


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    education: List[EducationResponse] = Field(default_factory=list)
    skills: List[SkillResponse] = Field(default_factory=list)
    projects: List[ProjectResponse] = Field(default_factory=list)
    certifications: List[CertificationResponse] = Field(default_factory=list)
    job_preference: Optional[JobPreferenceResponse] = None
    application_preference: Optional[ApplicationPreferenceResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProfileCompletenessResponse(BaseModel):
    percentage: int = Field(..., ge=0, le=100)
    missing_sections: List[str] = Field(default_factory=list)


class ProfileSummaryResponse(BaseModel):
    name: str
    roles: List[str]
    locations: List[str]
    skills: List[str]
    experience_years: float
    education_count: int
    projects_count: int
    certifications_count: int
    profile_completeness: int

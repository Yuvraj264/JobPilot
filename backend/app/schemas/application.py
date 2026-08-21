from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ApplicationCreate(BaseModel):
    job_id: int
    source_resume_id: Optional[int] = None
    tailored_resume_id: Optional[int] = None
    application_package_id: Optional[int] = None


class ApplicationResponse(BaseModel):
    id: int
    profile_id: int
    job_id: int
    match_id: Optional[int] = None
    application_package_id: Optional[int] = None
    selected_resume_id: Optional[int] = None
    tailored_resume_id: Optional[int] = None
    status: str
    source: str
    application_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationApprovalRequest(BaseModel):
    user_confirmed: bool = Field(..., description="Explicit user confirmation indicator")
    notes: Optional[str] = None


class ApplicationRejectRequest(BaseModel):
    rejection_reason: str


class ApplicationRequestChangesRequest(BaseModel):
    change_instructions: str


class SubmissionAuthorizationResponse(BaseModel):
    id: int
    application_id: int
    package_version: int
    status: str
    authorized_by: str
    authorized_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionRunResponse(BaseModel):
    id: int
    application_id: int
    authorization_id: Optional[int] = None
    adapter: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    state: str
    status: str
    submission_id: Optional[str] = None
    confirmation: Optional[str] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationTimelineResponse(BaseModel):
    application_id: int
    timeline: List[Dict[str, Any]]


class ApplicationSourceConfigurationResponse(BaseModel):
    id: int
    source_id: int
    enabled: bool
    mode: str
    allowed_domains: List[str]
    capabilities: Dict[str, bool]
    max_applications_per_run: int
    max_applications_per_day: int
    max_failed_attempts: int
    max_human_interventions: int
    require_human_review: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationSourceConfigurationUpdate(BaseModel):
    enabled: Optional[bool] = None
    mode: Optional[str] = None
    allowed_domains: Optional[List[str]] = None
    capabilities: Optional[Dict[str, bool]] = None
    max_applications_per_run: Optional[int] = None
    max_applications_per_day: Optional[int] = None
    max_failed_attempts: Optional[int] = None
    max_human_interventions: Optional[int] = None
    require_human_review: Optional[bool] = None


class HumanInterventionEventResponse(BaseModel):
    id: int
    application_id: int
    automation_run_id: Optional[int] = None
    type: str
    reason: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationQueueResponse(BaseModel):
    id: int
    application_id: int
    priority: float
    status: str
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BrowserStateResponse(BaseModel):
    application_id: int
    current_url: Optional[str] = None
    page_title: Optional[str] = None
    screenshots: List[str]
    state: str


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

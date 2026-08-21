from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TailoredResumeResponse(BaseModel):
    id: int
    profile_id: int
    source_resume_id: Optional[int] = None
    job_id: int
    version: int
    title: str
    status: str
    pdf_file_path: Optional[str] = None
    docx_file_path: Optional[str] = None
    relevance_score: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TailoredResumePreviewResponse(BaseModel):
    id: int
    title: str
    structured_content: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ChangeReportResponse(BaseModel):
    id: int
    change_report: Dict[str, Any]
    keyword_analysis: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ApplicationPackageResponse(BaseModel):
    id: int
    profile_id: int
    job_id: int
    source_resume_id: Optional[int] = None
    tailored_resume_id: Optional[int] = None
    status: str
    package_summary: Dict[str, Any] = Field(default_factory=dict)
    validation_result: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationPackageCreate(BaseModel):
    job_id: int
    source_resume_id: Optional[int] = None
    tailored_resume_id: Optional[int] = None

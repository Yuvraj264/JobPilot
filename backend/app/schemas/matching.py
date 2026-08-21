from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.job import JobResponse


class JobMatchResponse(BaseModel):
    id: int
    job_id: int
    profile_id: int
    overall_score: float
    recommendation: str
    eligible: bool
    confidence: float
    matcher_version: str
    component_scores: Dict[str, float] = Field(default_factory=dict)
    hard_failures: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    explanation: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobMatchDetailResponse(JobMatchResponse):
    job: JobResponse

    model_config = ConfigDict(from_attributes=True)


class MatchRunResponse(BaseModel):
    id: int
    profile_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    jobs_evaluated: int
    jobs_eligible: int
    apply_count: int
    review_count: int
    skip_count: int
    error_count: int
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MatchConfigResponse(BaseModel):
    id: int
    profile_id: int
    weight_skills: float
    weight_role: float
    weight_experience: float
    weight_location: float
    weight_workplace: float
    weight_employment: float
    weight_education: float
    weight_semantic: float
    threshold_apply: float
    threshold_review: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchConfigUpdate(BaseModel):
    weight_skills: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_role: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_experience: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_location: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_workplace: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_employment: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_education: Optional[float] = Field(None, ge=0.0, le=1.0)
    weight_semantic: Optional[float] = Field(None, ge=0.0, le=1.0)
    threshold_apply: Optional[float] = Field(None, ge=0.0, le=100.0)
    threshold_review: Optional[float] = Field(None, ge=0.0, le=100.0)


class MatchStatsResponse(BaseModel):
    jobs_evaluated: int
    eligible: int
    apply: int
    review: int
    skip: int
    average_score: float


class BatchMatchRequest(BaseModel):
    limit: int = Field(100, ge=1, le=500)

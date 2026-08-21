from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class JobSourceResponse(BaseModel):
    id: int
    name: str
    display_name: str
    source_type: str
    base_url: Optional[str] = None
    enabled: bool
    last_successful_run: Optional[datetime] = None
    last_failed_run: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobResponse(BaseModel):
    id: int
    source_id: Optional[int] = None
    external_job_id: Optional[str] = None
    title: str
    company_name: str
    company_url: Optional[str] = None
    job_url: Optional[str] = None
    location: Optional[str] = None
    normalized_location: Optional[str] = None
    employment_type: str
    workplace_type: str
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str
    posted_at: Optional[datetime] = None
    discovered_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(JobResponse):
    description: Optional[str] = None
    application_url: Optional[str] = None
    source_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class JobStatusUpdate(BaseModel):
    status: str  # DISCOVERED, ACTIVE, EXPIRED, CLOSED, DUPLICATE, POTENTIAL_DUPLICATE, INVALID, SKIPPED


class JobDiscoveryRunResponse(BaseModel):
    id: int
    source_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    jobs_discovered: int
    jobs_created: int
    jobs_updated: int
    duplicates: int
    invalid_jobs: int
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobStatsResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    duplicate_jobs: int
    potential_duplicates: int
    total_sources: int
    enabled_sources: int
    jobs_discovered_today: int


class DiscoverySummaryResponse(BaseModel):
    source: str
    status: str
    jobs_discovered: int
    jobs_created: int
    jobs_updated: int
    duplicates: int
    invalid_jobs: int


class SourceConfigurationResponse(BaseModel):
    id: int
    source_id: int
    enabled: bool
    discovery_enabled: bool
    application_enabled: bool
    max_jobs_per_run: int
    max_pages_per_run: int
    rate_limit: float
    configuration: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class SourceConfigurationUpdate(BaseModel):
    enabled: Optional[bool] = None
    discovery_enabled: Optional[bool] = None
    application_enabled: Optional[bool] = None
    max_jobs_per_run: Optional[int] = None
    max_pages_per_run: Optional[int] = None
    rate_limit: Optional[float] = None
    configuration: Optional[Dict[str, Any]] = None


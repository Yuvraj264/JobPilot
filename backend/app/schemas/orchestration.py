from datetime import datetime, date
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict


class OrchestrationRunResponse(BaseModel):
    id: int
    profile_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    trigger_type: str
    jobs_discovered: int
    jobs_matched: int
    jobs_selected: int
    packages_created: int
    applications_ready: int
    applications_approved: int
    applications_queued: int
    applications_submitted: int
    applications_failed: int
    applications_paused: int
    error_count: int
    configuration_version: str

    model_config = ConfigDict(from_attributes=True)


class AutomationConfigurationResponse(BaseModel):
    id: int
    profile_id: int
    preset_name: str
    is_active: bool
    discovery_enabled: bool
    discovery_sources: List[str]
    max_jobs_per_run: int
    minimum_match_score: float
    allowed_recommendations: List[str]
    auto_tailor_resume: bool
    auto_generate_answers: bool
    require_human_review: bool
    auto_approve: bool
    allowed_modes: List[str]
    max_applications_per_run: int
    max_applications_per_day: int
    dry_run: bool
    max_retries: int
    cooldown_days: int
    concurrency_limit: int
    priority_weights: Dict[str, float]
    authorization_expiration_hours: int

    model_config = ConfigDict(from_attributes=True)


class AutomationConfigurationUpdate(BaseModel):
    preset_name: Optional[str] = None
    is_active: Optional[bool] = None
    discovery_enabled: Optional[bool] = None
    discovery_sources: Optional[List[str]] = None
    max_jobs_per_run: Optional[int] = None
    minimum_match_score: Optional[float] = None
    allowed_recommendations: Optional[List[str]] = None
    auto_tailor_resume: Optional[bool] = None
    auto_generate_answers: Optional[bool] = None
    require_human_review: Optional[bool] = None
    auto_approve: Optional[bool] = None
    allowed_modes: Optional[List[str]] = None
    max_applications_per_run: Optional[int] = None
    max_applications_per_day: Optional[int] = None
    dry_run: Optional[bool] = None
    max_retries: Optional[int] = None
    cooldown_days: Optional[int] = None
    concurrency_limit: Optional[int] = None
    priority_weights: Optional[Dict[str, float]] = None
    authorization_expiration_hours: Optional[int] = None


class DailyAutomationMetricResponse(BaseModel):
    id: int
    profile_id: int
    date: date
    jobs_discovered: int
    jobs_matched: int
    applications_prepared: int
    applications_submitted: int
    applications_failed: int
    average_match_score: float

    model_config = ConfigDict(from_attributes=True)


class SchedulerStatusResponse(BaseModel):
    enabled: bool
    running: bool
    schedule_type: str
    scheduled_hour: int
    scheduled_minute: int
    selected_days: List[int]
    last_run_time: Optional[datetime] = None


class SchedulerConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    schedule_type: Optional[str] = None
    selected_days: Optional[List[int]] = None
    scheduled_hour: Optional[int] = None
    scheduled_minute: Optional[int] = None

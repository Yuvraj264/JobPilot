from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ActionLogResponse(BaseModel):
    id: int
    automation_run_id: int
    timestamp: datetime
    action_type: str
    field_type: Optional[str] = None
    target_selector: Optional[str] = None
    result: str
    confidence: float
    value_present: bool
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AutomationRunResponse(BaseModel):
    id: int
    profile_id: int
    job_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    state: str
    status: str
    current_url: Optional[str] = None
    actions_attempted: int
    actions_completed: int
    actions_failed: int
    human_intervention_required: bool
    pause_reason: Optional[str] = None
    error_message: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AutomationRunDetailResponse(AutomationRunResponse):
    action_logs: List[ActionLogResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AutomationStartRequest(BaseModel):
    job_id: int

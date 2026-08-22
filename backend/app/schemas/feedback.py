from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ApplicationFeedbackCreate(BaseModel):
    outcome: Optional[str] = Field(None, description="Outcome (e.g. response, interview, rejection, assessment, offer, withdrawal)")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="General user rating (1-5)")
    resume_rating: Optional[int] = Field(None, ge=1, le=5, description="Tailoring rating (1-5)")
    match_rating: Optional[int] = Field(None, ge=1, le=5, description="Match score transparency rating (1-5)")
    answer_rating: Optional[int] = Field(None, ge=1, le=5, description="Screening question answers rating (1-5)")
    notes: Optional[str] = Field(None, description="Free-text feedback notes")

class ApplicationFeedbackResponse(BaseModel):
    id: int
    application_id: int
    outcome: Optional[str] = None
    user_rating: Optional[int] = None
    resume_rating: Optional[int] = None
    match_rating: Optional[int] = None
    answer_rating: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ApplicationOutcomeUpdate(BaseModel):
    outcome: str = Field(..., description="Recruiter response outcome status")
    notes: Optional[str] = None

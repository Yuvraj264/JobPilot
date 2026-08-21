from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class QuestionAnalyzeRequest(BaseModel):
    question_text: str
    label: Optional[str] = ""
    field_identifier: Optional[str] = ""
    max_length: Optional[int] = None


class QuestionAnalyzeResponse(BaseModel):
    question_type: str
    classification_confidence: float
    answer_source: str
    is_sensitive: bool


class ApplicationAnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: Optional[str] = None
    answer_status: str
    confidence: float
    generated_by: str
    validation_result: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationQuestionResponse(BaseModel):
    id: int
    automation_run_id: Optional[int] = None
    job_id: Optional[int] = None
    question_text: str
    field_identifier: Optional[str] = None
    question_type: str
    required: bool
    classification_confidence: float
    answer_source: str
    max_length: Optional[int] = None
    is_sensitive: bool
    created_at: datetime
    answer: Optional[ApplicationAnswerResponse] = None

    model_config = ConfigDict(from_attributes=True)


class AnswerApproveRequest(BaseModel):
    answer_text: Optional[str] = None
    save_to_memory: bool = True


class AnswerProvideRequest(BaseModel):
    answer_text: str
    save_to_memory: bool = True

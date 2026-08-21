from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.profile_service import ProfileService
from app.services.screening.question_classifier import QuestionClassifier
from app.services.screening.answer_source_resolver import AnswerSourceResolver
from app.services.screening.question_processing_service import QuestionProcessingService
from app.services.screening.answer_validator import AnswerValidator
from app.models.screening import ApplicationQuestion, ApplicationAnswer, AnswerMemory
from app.schemas.screening import (
    QuestionAnalyzeRequest,
    QuestionAnalyzeResponse,
    ApplicationQuestionResponse,
    ApplicationAnswerResponse,
    AnswerApproveRequest,
    AnswerProvideRequest,
)

router = APIRouter(tags=["Screening Question Engine"])


@router.post("/api/questions/analyze", response_model=QuestionAnalyzeResponse)
def analyze_question(payload: QuestionAnalyzeRequest):
    """Analyze and classify screening question text without executing full automation run."""
    cls = QuestionClassifier.classify_question(
        payload.question_text,
        label=payload.label or "",
        field_identifier=payload.field_identifier or ""
    )
    source = AnswerSourceResolver.resolve_source(cls["type"], payload.question_text)
    return {
        "question_type": cls["type"],
        "classification_confidence": cls["confidence"],
        "answer_source": source,
        "is_sensitive": cls["is_sensitive"],
    }


@router.get("/api/questions/review", response_model=List[ApplicationQuestionResponse])
def get_pending_review_questions(db: Session = Depends(get_db)):
    """Retrieve all pending screening questions in the human review queue."""
    questions = (
        db.query(ApplicationQuestion)
        .join(ApplicationAnswer)
        .filter(ApplicationAnswer.answer_status.in_(["NEEDS_REVIEW", "INSUFFICIENT_INFORMATION"]))
        .order_by(ApplicationQuestion.created_at.desc())
        .all()
    )
    return questions


@router.get("/api/questions/{id}", response_model=ApplicationQuestionResponse)
def get_question(id: int, db: Session = Depends(get_db)):
    """Retrieve single question and its associated answer details."""
    question = db.query(ApplicationQuestion).filter(ApplicationQuestion.id == id).first()
    if not question:
        raise HTTPException(status_code=404, detail=f"ApplicationQuestion with ID {id} not found.")
    return question


@router.post("/api/questions/{id}/answer", response_model=ApplicationAnswerResponse)
def generate_question_answer(id: int, db: Session = Depends(get_db)):
    """Trigger answer generation pipeline for a specific stored question."""
    question = db.query(ApplicationQuestion).filter(ApplicationQuestion.id == id).first()
    if not question:
        raise HTTPException(status_code=404, detail=f"ApplicationQuestion with ID {id} not found.")

    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        from app.services.seed_service import seed_sample_profile
        profile = seed_sample_profile(db, user_id=1)

    processor = QuestionProcessingService()
    res = processor.process_question(
        db=db,
        question_text=question.question_text,
        profile=profile,
        job_context={"title": "Target Role", "company_name": "Target Company"},
        automation_run_id=question.automation_run_id,
        job_id=question.job_id,
        field_identifier=question.field_identifier,
        required=question.required,
        max_length=question.max_length,
        require_human_review=True
    )
    
    ans = db.query(ApplicationAnswer).filter(ApplicationAnswer.id == res["answer_id"]).first()
    return ans


@router.post("/api/questions/{id}/approve", response_model=ApplicationAnswerResponse)
def approve_question_answer(id: int, payload: AnswerApproveRequest, db: Session = Depends(get_db)):
    """Human user approves (or edits & approves) a generated answer."""
    question = db.query(ApplicationQuestion).filter(ApplicationQuestion.id == id).first()
    if not question or not question.answer:
        raise HTTPException(status_code=404, detail=f"Question or Answer with ID {id} not found.")

    profile = ProfileService.get_profile(db, user_id=1)

    ans = question.answer
    if payload.answer_text and payload.answer_text.strip():
        ans.answer_text = payload.answer_text.strip()
        ans.generated_by = "HUMAN"
    
    ans.answer_status = "READY"
    ans.confidence = 1.0
    db.commit()
    db.refresh(ans)

    # Save to AnswerMemory if user requested reuse
    if payload.save_to_memory and profile and ans.answer_text:
        existing_mem = db.query(AnswerMemory).filter(
            AnswerMemory.profile_id == profile.id,
            AnswerMemory.question_text == question.question_text
        ).first()
        if not existing_mem:
            mem = AnswerMemory(
                profile_id=profile.id,
                question_text=question.question_text,
                question_type=question.question_type,
                answer_text=ans.answer_text,
                user_approved=True,
                reusable=True
            )
            db.add(mem)
            db.commit()

    return ans


@router.post("/api/questions/{id}/reject", response_model=ApplicationAnswerResponse)
def reject_question_answer(id: int, db: Session = Depends(get_db)):
    """Human user rejects a generated answer."""
    question = db.query(ApplicationQuestion).filter(ApplicationQuestion.id == id).first()
    if not question or not question.answer:
        raise HTTPException(status_code=404, detail=f"Question or Answer with ID {id} not found.")

    ans = question.answer
    ans.answer_status = "REJECTED"
    db.commit()
    db.refresh(ans)
    return ans


@router.post("/api/answers/{id}/validate", response_model=ApplicationAnswerResponse)
def revalidate_answer(id: int, db: Session = Depends(get_db)):
    """Re-validate an existing answer record."""
    ans = db.query(ApplicationAnswer).filter(ApplicationAnswer.id == id).first()
    if not ans:
        raise HTTPException(status_code=404, detail=f"ApplicationAnswer {id} not found.")

    q_text = ans.question.question_text if ans.question else "Question"
    val_res = AnswerValidator.validate_answer(ans.answer_text, q_text, confidence=ans.confidence)
    ans.validation_result = val_res
    db.commit()
    db.refresh(ans)
    return ans

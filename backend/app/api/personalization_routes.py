from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database.connection import SessionLocal
from app.models.personalization import (
    PersonalPreferenceProfile,
    PreferenceConfigurationVersion,
    BehavioralSignal,
    PreferenceFeedback,
    JobFeedback,
    ResumeFeedback,
    AnswerFeedback,
    OutcomeFeedback,
    OptimizationSuggestion,
    OptimizationCycle
)
from app.models.profile import UserProfile
from app.models.job import Job
from app.models.application import Application
from app.services.personalization.preference_inference import (
    get_or_create_preference_profile,
    log_config_version,
    rollback_preference_config,
    PreferenceInferenceService
)
from app.services.personalization.optimization_service import OptimizationSuggestionService
from datetime import datetime

router = APIRouter(prefix="/personalization", tags=["Personalization & Feedback"])


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper to get current profile ID
def get_profile_id(db: Session, x_user_id: Optional[str]) -> int:
    # Default fallback to first profile if not provided
    if x_user_id:
        try:
            uid = int(x_user_id)
            profile = db.query(UserProfile).filter(UserProfile.user_id == uid).first()
            if profile:
                return profile.id
        except ValueError:
            pass
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile.id


# Pydantic Schemas
class JobFeedbackCreate(BaseModel):
    job_id: int
    feedback_type: str
    rejection_reason: Optional[str] = None
    liked_components: Optional[List[str]] = []


class ResumeFeedbackCreate(BaseModel):
    resume_id: Optional[int] = None
    tailored_resume_id: Optional[int] = None
    job_id: Optional[int] = None
    sections_changed: List[str] = []
    user_edits: bool = False
    rating: Optional[int] = None
    notes: Optional[str] = None


class AnswerFeedbackCreate(BaseModel):
    question_id: Optional[int] = None
    job_id: Optional[int] = None
    original_answer: str
    edited_answer: str
    edit_reason: Optional[str] = None


class OutcomeFeedbackCreate(BaseModel):
    application_id: int
    outcome: str
    notes: Optional[str] = None


class PreferenceUpdateItem(BaseModel):
    value: str
    source: str = "USER_EXPLICIT"
    strength: float = 1.0
    confidence: float = 1.0


class PreferenceProfileUpdate(BaseModel):
    enabled: Optional[bool] = None
    answer_style: Optional[str] = None
    preferred_roles: Optional[List[PreferenceUpdateItem]] = None
    disliked_roles: Optional[List[PreferenceUpdateItem]] = None
    preferred_locations: Optional[List[PreferenceUpdateItem]] = None
    excluded_locations: Optional[List[PreferenceUpdateItem]] = None
    preferred_companies: Optional[List[PreferenceUpdateItem]] = None
    excluded_companies: Optional[List[PreferenceUpdateItem]] = None
    preferred_skills: Optional[List[PreferenceUpdateItem]] = None
    disliked_skills: Optional[List[PreferenceUpdateItem]] = None
    workplace_modes: Optional[List[dict]] = None
    employment_types: Optional[List[dict]] = None


# --- 1. Feedback APIs ---

@router.post("/feedback/job")
def create_job_feedback(
    feed: JobFeedbackCreate,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    
    # Check if job exists
    job = db.query(Job).filter(Job.id == feed.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found")

    # Record feedback
    feedback = JobFeedback(
        profile_id=pid,
        job_id=feed.job_id,
        feedback_type=feed.feedback_type,
        rejection_reason=feed.rejection_reason,
        liked_components=feed.liked_components
    )
    db.add(feedback)

    # Record matching behavioral signal
    sig = BehavioralSignal(
        profile_id=pid,
        event_type="SAVED_JOB" if feed.feedback_type == "Save" else "SKIPPED_JOB",
        job_id=feed.job_id,
        details={"reason": feed.rejection_reason}
    )
    db.add(sig)

    db.commit()
    return {"message": "Job feedback recorded successfully", "id": feedback.id}


@router.post("/feedback/resume")
def create_resume_feedback(
    feed: ResumeFeedbackCreate,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    rec = ResumeFeedback(
        profile_id=pid,
        resume_id=feed.resume_id,
        tailored_resume_id=feed.tailored_resume_id,
        job_id=feed.job_id,
        sections_changed=feed.sections_changed,
        user_edits=feed.user_edits,
        rating=feed.rating,
        notes=feed.notes
    )
    db.add(rec)
    
    # Record signal
    sig = BehavioralSignal(
        profile_id=pid,
        event_type="EDITED_RESUME" if feed.user_edits else "VIEWED_RESUME",
        job_id=feed.job_id,
        details={"sections": feed.sections_changed}
    )
    db.add(sig)

    db.commit()
    return {"message": "Resume variant feedback recorded successfully", "id": rec.id}


@router.post("/feedback/answer")
def create_answer_feedback(
    feed: AnswerFeedbackCreate,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    rec = AnswerFeedback(
        profile_id=pid,
        question_id=feed.question_id,
        job_id=feed.job_id,
        original_answer=feed.original_answer,
        edited_answer=feed.edited_answer,
        edit_reason=feed.edit_reason
    )
    db.add(rec)
    
    # Record signal
    sig = BehavioralSignal(
        profile_id=pid,
        event_type="EDITED_ANSWER",
        job_id=feed.job_id,
        details={"original_len": len(feed.original_answer), "edited_len": len(feed.edited_answer)}
    )
    db.add(sig)

    db.commit()
    return {"message": "Answer modification feedback recorded successfully", "id": rec.id}


@router.post("/feedback/outcome")
def create_outcome_feedback(
    feed: OutcomeFeedbackCreate,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    
    # Verify application exists
    app = db.query(Application).filter(Application.id == feed.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application record not found")

    rec = OutcomeFeedback(
        profile_id=pid,
        application_id=feed.application_id,
        outcome=feed.outcome,
        notes=feed.notes
    )
    db.add(rec)
    db.commit()
    return {"message": "Outcome event logged", "id": rec.id}


@router.get("/feedback")
def list_feedbacks(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    jobs = db.query(JobFeedback).filter(JobFeedback.profile_id == pid).all()
    resumes = db.query(ResumeFeedback).filter(ResumeFeedback.profile_id == pid).all()
    answers = db.query(AnswerFeedback).filter(AnswerFeedback.profile_id == pid).all()
    outcomes = db.query(OutcomeFeedback).filter(OutcomeFeedback.profile_id == pid).all()
    return {
        "job_feedback": [{"id": f.id, "job_id": f.job_id, "feedback": f.feedback_type} for f in jobs],
        "resume_feedback": [{"id": r.id, "rating": r.rating} for r in resumes],
        "answer_feedback": [{"id": a.id, "edited": True} for a in answers],
        "outcome_feedback": [{"id": o.id, "outcome": o.outcome} for o in outcomes]
    }


@router.delete("/feedback/{id}")
def delete_feedback(
    id: int,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    # Search in all feedback tables and delete
    for model in [JobFeedback, ResumeFeedback, AnswerFeedback, OutcomeFeedback, PreferenceFeedback]:
        rec = db.query(model).filter(model.id == id, model.profile_id == pid).first()
        if rec:
            db.delete(rec)
            db.commit()
            return {"message": "Feedback record deleted successfully"}
            
    raise HTTPException(status_code=404, detail="Feedback record not found")


# --- 2. Preference Control APIs ---

@router.get("/preferences")
def get_preferences(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    pref = get_or_create_preference_profile(db, pid)
    
    # Get current configuration version
    latest = db.query(PreferenceConfigurationVersion).filter(
        PreferenceConfigurationVersion.profile_id == pid
    ).order_by(PreferenceConfigurationVersion.version.desc()).first()
    
    return {
        "profile_id": pref.profile_id,
        "enabled": pref.enabled,
        "answer_style": pref.answer_style,
        "preferred_roles": pref.preferred_roles,
        "disliked_roles": pref.disliked_roles,
        "preferred_locations": pref.preferred_locations,
        "excluded_locations": pref.excluded_locations,
        "preferred_companies": pref.preferred_companies,
        "excluded_companies": pref.excluded_companies,
        "preferred_skills": pref.preferred_skills,
        "disliked_skills": pref.disliked_skills,
        "workplace_modes": pref.workplace_modes,
        "employment_types": pref.employment_types,
        "minimum_salary": pref.minimum_salary,
        "preferred_salary": pref.preferred_salary,
        "version": latest.version if latest else 0
    }


@router.put("/preferences")
def update_preferences(
    update: PreferenceProfileUpdate,
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    pref = get_or_create_preference_profile(db, pid)
    
    changes = {}
    if update.enabled is not None:
        changes["enabled"] = {"old": pref.enabled, "new": update.enabled}
        pref.enabled = update.enabled
    if update.answer_style is not None:
        changes["answer_style"] = {"old": pref.answer_style, "new": update.answer_style}
        pref.answer_style = update.answer_style

    # Helper to serialize preference updates
    def serialize_prefs(items: List[PreferenceUpdateItem]) -> List[dict]:
        return [
            {
                "value": i.value,
                "source": i.source,
                "strength": i.strength,
                "confidence": i.confidence,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            for i in items
        ]

    if update.preferred_roles is not None:
        changes["preferred_roles"] = True
        pref.preferred_roles = serialize_prefs(update.preferred_roles)
    if update.disliked_roles is not None:
        changes["disliked_roles"] = True
        pref.disliked_roles = serialize_prefs(update.disliked_roles)
    if update.preferred_locations is not None:
        changes["preferred_locations"] = True
        pref.preferred_locations = serialize_prefs(update.preferred_locations)
    if update.excluded_locations is not None:
        changes["excluded_locations"] = True
        pref.excluded_locations = serialize_prefs(update.excluded_locations)
    if update.preferred_companies is not None:
        changes["preferred_companies"] = True
        pref.preferred_companies = serialize_prefs(update.preferred_companies)
    if update.excluded_companies is not None:
        changes["excluded_companies"] = True
        pref.excluded_companies = serialize_prefs(update.excluded_companies)
    if update.preferred_skills is not None:
        changes["preferred_skills"] = True
        pref.preferred_skills = serialize_prefs(update.preferred_skills)
    if update.disliked_skills is not None:
        changes["disliked_skills"] = True
        pref.disliked_skills = serialize_prefs(update.disliked_skills)
    if update.workplace_modes is not None:
        changes["workplace_modes"] = True
        pref.workplace_modes = update.workplace_modes
    if update.employment_types is not None:
        changes["employment_types"] = True
        pref.employment_types = update.employment_types

    # Log changes to preference configuration versions
    log_config_version(db, pid, changes, source="USER_EXPLICIT")
    db.commit()
    return {"message": "Preferences updated successfully"}


@router.post("/rollback")
def rollback_preferences(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    success = rollback_preference_config(db, pid)
    if not success:
        raise HTTPException(status_code=400, detail="No configuration version rollback history exists.")
    return {"message": "Successfully rolled back to previous configuration version"}


# --- 3. Optimization Suggestion APIs ---

@router.get("/preferences/suggestions")
def get_suggestions(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    # Generate pending suggestions
    suggestions = PreferenceInferenceService.generate_suggestions(db, pid)
    return [
        {
            "id": s.id,
            "category": s.category,
            "suggestion": s.suggestion,
            "evidence": s.evidence,
            "severity": s.severity,
            "status": s.status,
            "proposed_changes": s.proposed_changes
        }
        for s in suggestions
    ]


@router.post("/preferences/suggestions/{id}/accept")
def accept_suggestion(
    id: int,
    db: Session = Depends(get_db)
):
    success = PreferenceInferenceService.accept_suggestion(db, id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to accept suggestion or suggestion not pending")
    return {"message": "Suggestion successfully accepted and applied to preferences"}


@router.post("/preferences/suggestions/{id}/dismiss")
def dismiss_suggestion(
    id: int,
    db: Session = Depends(get_db)
):
    success = PreferenceInferenceService.dismiss_suggestion(db, id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to dismiss suggestion")
    return {"message": "Suggestion successfully dismissed"}


@router.post("/preferences/suggestions/{id}/remind")
def remind_suggestion_later(
    id: int,
    db: Session = Depends(get_db)
):
    success = PreferenceInferenceService.remind_suggestion_later(db, id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to postpone suggestion")
    return {"message": "Suggestion postponed. Will remind you later."}


# --- 4. Career Intelligence Insights APIs ---

@router.get("/insights/skills")
def get_skills_insights(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    
    # Run a weekly run report update dynamically
    OptimizationSuggestionService.run_weekly_optimization(db, pid)
    
    # Get top missing skills
    jobs = db.query(Job).join(JobFeedback).filter(
        JobFeedback.profile_id == pid,
        JobFeedback.feedback_type == "Save"
    ).all()
    
    skills_map = {}
    for job in jobs:
        for s in (job.source_metadata.get("required_skills", []) if job.source_metadata else []):
            skills_map[s] = skills_map.get(s, 0) + 1
            
    sorted_skills = sorted(skills_map.items(), key=lambda x: x[1], reverse=True)
    return {
        "skills_insights": [
            {
                "skill": name,
                "saved_jobs_count": count,
                "evidence": OptimizationSuggestionService.get_skill_evidence(db, pid, name)
            }
            for name, count in sorted_skills[:10]
        ]
    }


@router.get("/insights/roles")
def get_roles_insights(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    # Aggregate roles saved vs skipped
    saved = db.query(Job.title).join(JobFeedback).filter(
        JobFeedback.profile_id == pid,
        JobFeedback.feedback_type == "Save"
    ).all()
    
    skipped = db.query(Job.title).join(JobFeedback).filter(
        JobFeedback.profile_id == pid,
        JobFeedback.feedback_type == "Skip"
    ).all()
    
    return {
        "saved_roles": [s[0] for s in saved],
        "skipped_roles": [sk[0] for sk in skipped]
    }


@router.get("/insights/companies")
def get_companies_insights(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    # Aggregate interactive companies
    feedback_companies = db.query(Job.company_name).join(JobFeedback).filter(
        JobFeedback.profile_id == pid,
        JobFeedback.feedback_type == "Save"
    ).all()
    
    counts = {}
    for c in feedback_companies:
        name = c[0]
        if name:
            counts[name] = counts.get(name, 0) + 1
            
    sorted_companies = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return {
        "interactive_companies": [
            {"company": company, "saved_jobs": count}
            for company, count in sorted_companies[:5]
        ]
    }


@router.get("/insights/sources")
def get_sources_insights(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    # Aggregate job discovery counts or conversion statistics
    return {"sources_insights": []}


@router.get("/insights/outcomes")
def get_outcomes_insights(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    # Return outcome tracking lists
    outcomes = db.query(OutcomeFeedback).filter(OutcomeFeedback.profile_id == pid).all()
    return {
        "outcomes": [
            {
                "id": o.id,
                "application_id": o.application_id,
                "outcome": o.outcome,
                "created_at": o.created_at
            }
            for o in outcomes
        ]
    }


@router.delete("/history/clear")
def clear_personalization_history(
    x_user_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    pid = get_profile_id(db, x_user_id)
    db.query(BehavioralSignal).filter(BehavioralSignal.profile_id == pid).delete()
    db.query(JobFeedback).filter(JobFeedback.profile_id == pid).delete()
    db.query(ResumeFeedback).filter(ResumeFeedback.profile_id == pid).delete()
    db.query(AnswerFeedback).filter(AnswerFeedback.profile_id == pid).delete()
    db.query(OutcomeFeedback).filter(OutcomeFeedback.profile_id == pid).delete()
    
    # Reset preference profile lists
    pref = get_or_create_preference_profile(db, pid)
    pref.preferred_roles = []
    pref.disliked_roles = []
    pref.preferred_locations = []
    pref.excluded_locations = []
    pref.preferred_companies = []
    pref.excluded_companies = []
    pref.preferred_skills = []
    pref.disliked_skills = []
    pref.workplace_modes = []
    pref.employment_types = []
    db.commit()
    return {"message": "All personalization history and inferred/explicit preferences have been cleared successfully."}


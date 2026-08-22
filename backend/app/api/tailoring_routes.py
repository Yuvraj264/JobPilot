from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.profile_service import ProfileService
from app.services.tailoring.resume_tailoring_service import ResumeTailoringService
from app.services.tailoring.package_service import ApplicationPackageService
from app.models.resume import Resume
from app.models.job import Job
from app.models.tailoring import TailoredResume, ApplicationPackage
from app.schemas.tailoring import (
    TailoredResumeResponse,
    TailoredResumePreviewResponse,
    ChangeReportResponse,
    ApplicationPackageResponse,
    ApplicationPackageCreate,
)

router = APIRouter(tags=["Resume Tailoring & Application Packages"])


from app.api.auth import get_current_user_id

router = APIRouter(tags=["Resume Tailoring & Application Packages"])


def get_profile_by_user(db: Session, user_id: int) -> int:
    profile = ProfileService.get_profile(db, user_id=user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UserProfile not found. Please create a profile first."
        )
    return profile


@router.post("/api/resumes/{resume_id}/tailor/{job_id}", response_model=TailoredResumeResponse)
def tailor_resume_for_job(resume_id: int, job_id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Trigger job-specific resume tailoring pipeline."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")

    profile = get_profile_by_user(db, current_user_id)
    master_resume = db.query(Resume).filter(Resume.id == resume_id, Resume.profile_id == profile.id).first()
    if not master_resume:
        raise HTTPException(status_code=404, detail="Master resume not found.")

    try:
        tailored = ResumeTailoringService.tailor_resume(db, profile, job, master_resume)
        return tailored
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/api/tailored-resumes", response_model=List[TailoredResumeResponse])
def list_tailored_resumes(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """List all generated tailored resumes for the current profile."""
    profile = get_profile_by_user(db, current_user_id)
    return db.query(TailoredResume).filter(TailoredResume.profile_id == profile.id).order_by(TailoredResume.created_at.desc()).all()


@router.get("/api/tailored-resumes/{id}", response_model=TailoredResumeResponse)
def get_tailored_resume(id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Retrieve single tailored resume record."""
    profile = get_profile_by_user(db, current_user_id)
    rec = db.query(TailoredResume).filter(TailoredResume.id == id, TailoredResume.profile_id == profile.id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"TailoredResume {id} not found.")
    return rec


@router.get("/api/tailored-resumes/{id}/preview", response_model=TailoredResumePreviewResponse)
def get_tailored_resume_preview(id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Retrieve intermediate structured ResumeDocument content for UI preview."""
    profile = get_profile_by_user(db, current_user_id)
    rec = db.query(TailoredResume).filter(TailoredResume.id == id, TailoredResume.profile_id == profile.id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"TailoredResume {id} not found.")
    return {
        "id": rec.id,
        "title": rec.title,
        "structured_content": rec.structured_content
    }


@router.get("/api/tailored-resumes/{id}/changes", response_model=ChangeReportResponse)
def get_tailored_resume_changes(id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Retrieve change report and keyword coverage analysis."""
    profile = get_profile_by_user(db, current_user_id)
    rec = db.query(TailoredResume).filter(TailoredResume.id == id, TailoredResume.profile_id == profile.id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"TailoredResume {id} not found.")
    return {
        "id": rec.id,
        "change_report": rec.change_report,
        "keyword_analysis": rec.keyword_analysis
    }


@router.get("/api/tailored-resumes/{id}/validation")
def get_tailored_resume_validation(id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Retrieve truthfulness validation status for tailored resume."""
    profile = get_profile_by_user(db, current_user_id)
    rec = db.query(TailoredResume).filter(TailoredResume.id == id, TailoredResume.profile_id == profile.id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"TailoredResume {id} not found.")
    return {
        "id": rec.id,
        "status": rec.status,
        "valid": rec.status == "VALIDATED"
    }


@router.post("/api/application-packages", response_model=ApplicationPackageResponse)
def create_application_package(payload: ApplicationPackageCreate, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Assemble an ApplicationPackage for target job."""
    profile = get_profile_by_user(db, current_user_id)

    try:
        pkg = ApplicationPackageService.create_package(
            db,
            profile_id=profile.id,
            job_id=payload.job_id,
            source_resume_id=payload.source_resume_id,
            tailored_resume_id=payload.tailored_resume_id
        )
        return pkg
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/application-packages", response_model=List[ApplicationPackageResponse])
def list_application_packages(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """List all application packages."""
    profile = get_profile_by_user(db, current_user_id)
    return db.query(ApplicationPackage).filter(ApplicationPackage.profile_id == profile.id).order_by(ApplicationPackage.created_at.desc()).all()


@router.get("/api/application-packages/{id}", response_model=ApplicationPackageResponse)
def get_application_package(id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Retrieve single application package details."""
    profile = get_profile_by_user(db, current_user_id)
    pkg = db.query(ApplicationPackage).filter(ApplicationPackage.id == id, ApplicationPackage.profile_id == profile.id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail=f"ApplicationPackage {id} not found.")
    return pkg


@router.post("/api/application-packages/{id}/validate")
def validate_application_package(id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    """Validate readiness of application package."""
    profile = get_profile_by_user(db, current_user_id)
    pkg = db.query(ApplicationPackage).filter(ApplicationPackage.id == id, ApplicationPackage.profile_id == profile.id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail=f"ApplicationPackage {id} not found.")
    res = ApplicationPackageService.validate_package(db, id)
    return res

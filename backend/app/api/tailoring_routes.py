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


@router.post("/api/resumes/{resume_id}/tailor/{job_id}", response_model=TailoredResumeResponse)
def tailor_resume_for_job(resume_id: int, job_id: int, db: Session = Depends(get_db)):
    """Trigger job-specific resume tailoring pipeline."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")

    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        from app.services.seed_service import seed_sample_profile
        profile = seed_sample_profile(db, user_id=1)

    master_resume = db.query(Resume).filter(Resume.id == resume_id).first()

    try:
        tailored = ResumeTailoringService.tailor_resume(db, profile, job, master_resume)
        return tailored
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/api/tailored-resumes", response_model=List[TailoredResumeResponse])
def list_tailored_resumes(db: Session = Depends(get_db)):
    """List all generated tailored resumes."""
    return db.query(TailoredResume).order_by(TailoredResume.created_at.desc()).all()


@router.get("/api/tailored-resumes/{id}", response_model=TailoredResumeResponse)
def get_tailored_resume(id: int, db: Session = Depends(get_db)):
    """Retrieve single tailored resume record."""
    rec = db.query(TailoredResume).filter(TailoredResume.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"TailoredResume {id} not found.")
    return rec


@router.get("/api/tailored-resumes/{id}/preview", response_model=TailoredResumePreviewResponse)
def get_tailored_resume_preview(id: int, db: Session = Depends(get_db)):
    """Retrieve intermediate structured ResumeDocument content for UI preview."""
    rec = db.query(TailoredResume).filter(TailoredResume.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"TailoredResume {id} not found.")
    return {
        "id": rec.id,
        "title": rec.title,
        "structured_content": rec.structured_content
    }


@router.get("/api/tailored-resumes/{id}/changes", response_model=ChangeReportResponse)
def get_tailored_resume_changes(id: int, db: Session = Depends(get_db)):
    """Retrieve change report and keyword coverage analysis."""
    rec = db.query(TailoredResume).filter(TailoredResume.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"TailoredResume {id} not found.")
    return {
        "id": rec.id,
        "change_report": rec.change_report,
        "keyword_analysis": rec.keyword_analysis
    }


@router.get("/api/tailored-resumes/{id}/validation")
def get_tailored_resume_validation(id: int, db: Session = Depends(get_db)):
    """Retrieve truthfulness validation status for tailored resume."""
    rec = db.query(TailoredResume).filter(TailoredResume.id == id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"TailoredResume {id} not found.")
    return {
        "id": rec.id,
        "status": rec.status,
        "valid": rec.status == "VALIDATED"
    }


@router.post("/api/application-packages", response_model=ApplicationPackageResponse)
def create_application_package(payload: ApplicationPackageCreate, db: Session = Depends(get_db)):
    """Assemble an ApplicationPackage for target job."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        from app.services.seed_service import seed_sample_profile
        profile = seed_sample_profile(db, user_id=1)

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
def list_application_packages(db: Session = Depends(get_db)):
    """List all application packages."""
    return db.query(ApplicationPackage).order_by(ApplicationPackage.created_at.desc()).all()


@router.get("/api/application-packages/{id}", response_model=ApplicationPackageResponse)
def get_application_package(id: int, db: Session = Depends(get_db)):
    """Retrieve single application package details."""
    pkg = db.query(ApplicationPackage).filter(ApplicationPackage.id == id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail=f"ApplicationPackage {id} not found.")
    return pkg


@router.post("/api/application-packages/{id}/validate")
def validate_application_package(id: int, db: Session = Depends(get_db)):
    """Validate readiness of application package."""
    res = ApplicationPackageService.validate_package(db, id)
    return res

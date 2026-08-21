import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.profile_service import ProfileService
from app.services.storage_service import StorageService
from app.services.resume_service import ResumeService
from app.services.resume_processing_service import ResumeProcessingService
from app.services.consistency_service import ConsistencyService
from app.services.quality_service import QualityService
from app.schemas.resume import (
    ResumeResponse,
    ResumeParsedDetailResponse,
    ResumeStatusResponse,
    ResumeQualityResponse,
    ResumeConsistencyResponse,
)

router = APIRouter(prefix="/api/resumes", tags=["Resume Management"])


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    name: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a new resume (PDF or DOCX), save securely, and execute processing pipeline.
    """
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        # Auto-create user profile if missing
        from app.schemas.profile import ProfileCreate
        profile = ProfileService.create_profile(db, ProfileCreate(full_name="User Candidate", email="candidate@example.com"), user_id=1)

    file_bytes = await file.read()
    filename = file.filename or "resume.pdf"
    display_name = name or os.path.splitext(filename)[0]

    try:
        relative_path, file_type, file_size = StorageService.save_file(
            file_bytes=file_bytes,
            original_filename=filename,
            user_id=1,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

    # Create Resume DB Record
    resume = ResumeService.create_resume_record(
        db=db,
        profile_id=profile.id,
        name=display_name,
        original_filename=filename,
        file_path=relative_path,
        file_type=file_type,
        file_size=file_size,
    )

    # Synchronously execute processing pipeline
    ResumeProcessingService.process_resume(db, resume)
    return resume


@router.get("", response_model=List[ResumeResponse])
def list_resumes(db: Session = Depends(get_db)):
    """List all uploaded resumes for the current profile."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        return []
    return ResumeService.get_resumes_by_profile(db, profile.id)


@router.get("/{id}", response_model=ResumeResponse)
def get_resume(id: int, db: Session = Depends(get_db)):
    """Retrieve metadata for a specific resume."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    resume = ResumeService.get_resume_by_id(db, resume_id=id, profile_id=profile.id)
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume with ID {id} not found.")
    return resume


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(id: int, db: Session = Depends(get_db)):
    """Delete resume metadata and underlying storage file."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    deleted = ResumeService.delete_resume(db, resume_id=id, profile_id=profile.id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Resume with ID {id} not found.")
    return None


@router.get("/{id}/status", response_model=ResumeStatusResponse)
def get_resume_status(id: int, db: Session = Depends(get_db)):
    """Check processing status of a resume."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    resume = ResumeService.get_resume_by_id(db, resume_id=id, profile_id=profile.id)
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume with ID {id} not found.")
    return resume


@router.get("/{id}/parsed", response_model=ResumeParsedDetailResponse)
def get_resume_parsed_details(id: int, db: Session = Depends(get_db)):
    """Retrieve structured parsed data (skills, education, experiences, projects, certifications)."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    resume = ResumeService.get_resume_by_id(db, resume_id=id, profile_id=profile.id)
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume with ID {id} not found.")
    return resume


@router.get("/{id}/quality", response_model=ResumeQualityResponse)
def get_resume_quality(id: int, db: Session = Depends(get_db)):
    """Run deterministic quality score analysis on a processed resume."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    resume = ResumeService.get_resume_by_id(db, resume_id=id, profile_id=profile.id)
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume with ID {id} not found.")
    return QualityService.analyze_quality(resume)


@router.get("/{id}/consistency", response_model=ResumeConsistencyResponse)
def get_resume_consistency(id: int, db: Session = Depends(get_db)):
    """Compare resume against canonical User Profile to detect skill/education/experience mismatches."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    resume = ResumeService.get_resume_by_id(db, resume_id=id, profile_id=profile.id)
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume with ID {id} not found.")
    return ConsistencyService.check_consistency(profile, resume)


@router.post("/{id}/reprocess", response_model=ResumeResponse)
def reprocess_resume(id: int, db: Session = Depends(get_db)):
    """Trigger re-running the extraction and section parsing pipeline on an existing resume."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    resume = ResumeService.get_resume_by_id(db, resume_id=id, profile_id=profile.id)
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume with ID {id} not found.")

    return ResumeProcessingService.process_resume(db, resume)


@router.post("/{id}/set-default", response_model=ResumeResponse)
def set_default_resume(id: int, db: Session = Depends(get_db)):
    """Set the selected resume as preferred default."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    updated = ResumeService.set_default_resume(db, resume_id=id, profile_id=profile.id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Resume with ID {id} not found.")
    return updated


@router.get("/{id}/download")
def download_resume(id: int, db: Session = Depends(get_db)):
    """Securely download resume document file."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    resume = ResumeService.get_resume_by_id(db, resume_id=id, profile_id=profile.id)
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume with ID {id} not found.")

    try:
        abs_path = StorageService.resolve_path(resume.file_path)
    except ValueError as err:
        raise HTTPException(status_code=403, detail=str(err))

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Physical resume file missing from storage.")

    media_type = "application/pdf" if resume.file_type == "PDF" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(path=abs_path, filename=resume.original_filename, media_type=media_type)

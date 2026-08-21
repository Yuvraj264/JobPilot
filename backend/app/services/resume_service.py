from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.resume import (
    Resume,
    ResumeSkill,
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
    ResumeCertification,
    ResumeProcessingEvent,
)
from app.services.storage_service import StorageService


class ResumeService:
    """
    Database CRUD operations and lifecycle management for Resume records.
    """

    @staticmethod
    def create_resume_record(
        db: Session,
        profile_id: int,
        name: str,
        original_filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
    ) -> Resume:
        # Check if this is the first resume for profile
        existing_count = db.query(Resume).filter(Resume.profile_id == profile_id).count()
        is_default = (existing_count == 0)

        resume = Resume(
            profile_id=profile_id,
            name=name,
            original_filename=original_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            is_default=is_default,
            processing_status="UPLOADED",
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # Log upload event
        event = ResumeProcessingEvent(
            resume_id=resume.id,
            event_type="UPLOAD",
            message=f"Resume '{original_filename}' uploaded successfully.",
        )
        db.add(event)
        db.commit()

        return resume

    @staticmethod
    def get_resumes_by_profile(db: Session, profile_id: int) -> List[Resume]:
        return db.query(Resume).filter(Resume.profile_id == profile_id).order_by(Resume.created_at.desc()).all()

    @staticmethod
    def get_resume_by_id(db: Session, resume_id: int, profile_id: int) -> Optional[Resume]:
        return db.query(Resume).filter(Resume.id == resume_id, Resume.profile_id == profile_id).first()

    @staticmethod
    def set_default_resume(db: Session, resume_id: int, profile_id: int) -> Optional[Resume]:
        target = ResumeService.get_resume_by_id(db, resume_id, profile_id)
        if not target:
            return None

        # Reset all other resumes for this profile
        db.query(Resume).filter(Resume.profile_id == profile_id).update({"is_default": False})
        target.is_default = True
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def delete_resume(db: Session, resume_id: int, profile_id: int) -> bool:
        resume = ResumeService.get_resume_by_id(db, resume_id, profile_id)
        if not resume:
            return False

        # Delete file from storage
        StorageService.delete(resume.file_path)

        was_default = resume.is_default
        db.delete(resume)
        db.commit()

        # If deleted resume was default, assign default to another resume if available
        if was_default:
            next_resume = db.query(Resume).filter(Resume.profile_id == profile_id).first()
            if next_resume:
                next_resume.is_default = True
                db.commit()

        return True

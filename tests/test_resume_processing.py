import os
import pytest
from app.database.connection import SessionLocal
from app.services.profile_service import ProfileService
from app.schemas.profile import ProfileCreate
from app.services.storage_service import StorageService
from app.services.resume_service import ResumeService
from app.services.resume_processing_service import ResumeProcessingService


def test_resume_processing_pipeline():
    """Test full processing pipeline transition from UPLOADED -> PROCESSED."""
    db = SessionLocal()
    try:
        profile = ProfileService.create_profile(db, ProfileCreate(full_name="Proc User", email="proc@example.com"), user_id=1)

        # Upload synthetic file
        pdf_fixture = "tests/fixtures/sample_resume_one_page.pdf"
        with open(pdf_fixture, "rb") as f:
            pdf_bytes = f.read()

        rel_path, file_type, file_size = StorageService.save_file(pdf_bytes, "sample_resume_one_page.pdf", user_id=1)

        resume = ResumeService.create_resume_record(
            db=db,
            profile_id=profile.id,
            name="Test Pipeline Resume",
            original_filename="sample_resume_one_page.pdf",
            file_path=rel_path,
            file_type=file_type,
            file_size=file_size,
        )
        assert resume.processing_status == "UPLOADED"

        # Execute processing pipeline
        processed_resume = ResumeProcessingService.process_resume(db, resume)
        assert processed_resume.processing_status == "PROCESSED"
        assert len(processed_resume.skills) > 0
        assert len(processed_resume.education) > 0

    finally:
        db.close()

import pytest
from app.database.connection import SessionLocal
from app.services.profile_service import ProfileService
from app.schemas.profile import ProfileCreate
from app.services.storage_service import StorageService
from app.services.resume_service import ResumeService
from app.services.resume_processing_service import ResumeProcessingService
from app.services.quality_service import QualityService


def test_quality_analysis():
    """Test deterministic resume quality score calculation."""
    db = SessionLocal()
    try:
        profile = ProfileService.create_profile(db, ProfileCreate(full_name="Qual User", email="qual@example.com"), user_id=1)

        pdf_fixture = "tests/fixtures/sample_resume_one_page.pdf"
        with open(pdf_fixture, "rb") as f:
            pdf_bytes = f.read()

        rel_path, file_type, file_size = StorageService.save_file(pdf_bytes, "sample_resume_one_page.pdf", user_id=1)
        resume = ResumeService.create_resume_record(
            db=db,
            profile_id=profile.id,
            name="Quality Test Resume",
            original_filename="sample_resume_one_page.pdf",
            file_path=rel_path,
            file_type=file_type,
            file_size=file_size,
        )
        ResumeProcessingService.process_resume(db, resume)

        quality = QualityService.analyze_quality(resume)
        assert "score" in quality
        assert isinstance(quality["score"], int)
        assert quality["score"] > 50
        assert "skills_detected" in quality

    finally:
        db.close()

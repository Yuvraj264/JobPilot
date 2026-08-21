import pytest
from app.database.connection import SessionLocal
from app.services.profile_service import ProfileService
from app.services.seed_service import seed_sample_profile
from app.services.storage_service import StorageService
from app.services.resume_service import ResumeService
from app.services.resume_processing_service import ResumeProcessingService
from app.services.consistency_service import ConsistencyService


def test_consistency_checker():
    """Test detecting mismatches between UserProfile and Parsed Resume."""
    db = SessionLocal()
    try:
        profile = seed_sample_profile(db, user_id=1)

        # Upload incomplete resume to trigger mismatch findings
        pdf_fixture = "tests/fixtures/sample_resume_incomplete.pdf"
        with open(pdf_fixture, "rb") as f:
            pdf_bytes = f.read()

        rel_path, file_type, file_size = StorageService.save_file(pdf_bytes, "sample_resume_incomplete.pdf", user_id=1)
        resume = ResumeService.create_resume_record(
            db=db,
            profile_id=profile.id,
            name="Incomplete Test Resume",
            original_filename="sample_resume_incomplete.pdf",
            file_path=rel_path,
            file_type=file_type,
            file_size=file_size,
        )
        ResumeProcessingService.process_resume(db, resume)

        report = ConsistencyService.check_consistency(profile, resume)
        assert "status" in report
        assert "issues" in report
        assert report["total_issues"] > 0
        issue_types = [i["type"] for i in report["issues"]]
        assert "SKILL_MISSING_FROM_RESUME" in issue_types

    finally:
        db.close()

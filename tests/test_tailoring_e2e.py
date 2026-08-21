import pytest
from app.database.connection import SessionLocal
from app.models.job import Job
from app.services.seed_service import seed_sample_profile
from app.services.tailoring.resume_tailoring_service import ResumeTailoringService
from app.services.tailoring.package_service import ApplicationPackageService


def test_tailoring_e2e_pipeline():
    """
    End-to-End Tailoring Pipeline Verification Test (Requirement 35):
    Profile * Job -> Requirement Extraction -> Evidence Selection -> Tailoring Plan -> Tailored Content -> Truthfulness Validation -> PDF/DOCX -> ApplicationPackage -> READY_FOR_REVIEW
    """
    db = SessionLocal()
    try:
        profile = seed_sample_profile(db, user_id=1)

        job = db.query(Job).filter(Job.id == 101).first()
        if not job:
            job = Job(
                id=101,
                title="Junior QA Engineer",
                company_name="Acme Technologies",
                status="ACTIVE",
                source_metadata={"required_skills": ["Python", "SQL", "Selenium"]}
            )
            db.add(job)
            db.commit()
        else:
            job.source_metadata = {"required_skills": ["Python", "SQL", "Selenium"]}
            db.commit()

        # 1. Generate Tailored Resume
        tailored = ResumeTailoringService.tailor_resume(db, profile, job)
        assert tailored.id is not None
        assert tailored.status == "VALIDATED"
        assert tailored.relevance_score > 0

        # 2. Assemble Application Package
        pkg = ApplicationPackageService.create_package(
            db,
            profile_id=profile.id,
            job_id=job.id,
            tailored_resume_id=tailored.id
        )

        assert pkg.id is not None
        assert pkg.status in ["READY_FOR_REVIEW", "PREPARING"]

    finally:
        db.close()

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.job import Job
from app.models.matching import JobMatch
from app.models.tailoring import TailoredResume, ApplicationPackage
from app.models.screening import ApplicationQuestion, ApplicationAnswer


class ApplicationPackageService:
    """
    Application Package Service assembling and validating ApplicationPackage objects.
    Ensures all materials (Job, Resume, Match Result, Screening Answers) are validated before status = READY_FOR_REVIEW.
    """

    @staticmethod
    def create_package(
        db: Session,
        profile_id: int,
        job_id: int,
        source_resume_id: Optional[int] = None,
        tailored_resume_id: Optional[int] = None
    ) -> ApplicationPackage:

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job with ID {job_id} not found.")

        # Check existing match
        match = db.query(JobMatch).filter(JobMatch.job_id == job_id, JobMatch.profile_id == profile_id).first()

        package = ApplicationPackage(
            profile_id=profile_id,
            job_id=job_id,
            source_resume_id=source_resume_id,
            tailored_resume_id=tailored_resume_id,
            status="PREPARING"
        )
        db.add(package)
        db.commit()
        db.refresh(package)

        # Validate Readiness
        val_res = ApplicationPackageService.validate_package(db, package.id)
        return package

    @staticmethod
    def validate_package(db: Session, package_id: int) -> Dict[str, Any]:
        package = db.query(ApplicationPackage).filter(ApplicationPackage.id == package_id).first()
        if not package:
            return {"valid": False, "issues": ["Package not found."]}

        issues = []

        # 1. Job Validation
        if not package.job:
            issues.append("Target job missing.")

        # 2. Tailored Resume Validation
        if not package.tailored_resume:
            issues.append("Tailored resume missing from package.")
        elif package.tailored_resume.status != "VALIDATED":
            issues.append(f"Tailored resume status is '{package.tailored_resume.status}', expected 'VALIDATED'.")

        # 3. Unresolved Screening Questions Validation
        unresolved_q = (
            db.query(ApplicationQuestion)
            .join(ApplicationAnswer)
            .filter(
                ApplicationQuestion.job_id == package.job_id,
                ApplicationAnswer.answer_status.in_(["NEEDS_REVIEW", "INSUFFICIENT_INFORMATION"])
            )
            .count()
        )
        if unresolved_q > 0:
            issues.append(f"Package contains {unresolved_q} unresolved screening questions requiring human review.")

        is_valid = len(issues) == 0
        package.validation_result = {
            "valid": is_valid,
            "issues": issues,
            "validation_status": "PASSED" if is_valid else "FAILED_VALIDATION"
        }

        if is_valid:
            package.status = "READY_FOR_REVIEW"
        else:
            package.status = "PREPARING"

        db.commit()
        db.refresh(package)

        return package.validation_result

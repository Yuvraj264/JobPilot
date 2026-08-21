from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.job import Job
from app.models.tailoring import TailoredResume, ApplicationPackage
from app.models.screening import ApplicationQuestion, ApplicationAnswer


class ApplicationValidationService:
    """
    Application Validation Service evaluating job, profile, resume, tailored resume,
    screening questions, and package internal consistency.
    Categorizes findings into BLOCKING vs WARNING.
    """

    @staticmethod
    def validate_application(
        db: Session,
        job: Optional[Job],
        profile: Optional[UserProfile],
        source_resume: Optional[Resume] = None,
        tailored_resume: Optional[TailoredResume] = None,
        package: Optional[ApplicationPackage] = None
    ) -> Dict[str, Any]:
        blocking = []
        warnings = []

        # 1. Job Checks
        if not job:
            blocking.append("BLOCKING: Target Job does not exist.")
        else:
            if not job.job_url and not job.application_url:
                blocking.append("BLOCKING: Job has no valid target URL or application URL.")
            if job.status == "EXPIRED" or job.status == "CLOSED":
                blocking.append(f"BLOCKING: Target Job status is '{job.status}'.")
            if job.workplace_type == "UNKNOWN":
                warnings.append("WARNING: Job workplace arrangement is UNKNOWN.")

        # 2. Profile Checks
        if not profile:
            blocking.append("BLOCKING: Candidate UserProfile missing.")
        else:
            if not profile.email or "@" not in profile.email:
                blocking.append("BLOCKING: Candidate email is missing or invalid.")
            if not profile.full_name:
                blocking.append("BLOCKING: Candidate full name is missing.")

        # 3. Source Resume Checks
        if source_resume:
            if source_resume.status != "PROCESSED":
                blocking.append(f"BLOCKING: Source Resume status is '{source_resume.status}', expected 'PROCESSED'.")

        # 4. Tailored Resume Checks
        if tailored_resume:
            if tailored_resume.status != "VALIDATED":
                blocking.append(f"BLOCKING: Tailored Resume status is '{tailored_resume.status}', expected 'VALIDATED'.")
            if tailored_resume.relevance_score < 30.0:
                warnings.append(f"WARNING: Tailored Resume relevance score is relatively low ({tailored_resume.relevance_score}%).")
        else:
            warnings.append("WARNING: No Tailored Resume associated with application.")

        # 5. Screening Question Checks
        if job:
            questions = db.query(ApplicationQuestion).filter(ApplicationQuestion.job_id == job.id).all()
            for q in questions:
                ans = db.query(ApplicationAnswer).filter(ApplicationAnswer.question_id == q.id).first()
                if q.is_required and not ans:
                    blocking.append(f"BLOCKING: Required screening question '{q.question_text[:40]}...' is unanswered.")
                elif ans and ans.answer_status in ["NEEDS_REVIEW", "INSUFFICIENT_INFORMATION"]:
                    blocking.append(f"BLOCKING: Screening question '{q.question_text[:40]}...' requires human review.")
                elif ans and not ans.answer_text:
                    blocking.append(f"BLOCKING: Answer for required question '{q.question_text[:40]}...' is empty.")

        is_valid = len(blocking) == 0
        return {
            "valid": is_valid,
            "blocking_issues": blocking,
            "warnings": warnings,
            "validation_status": "PASSED" if is_valid else "FAILED_BLOCKING_ISSUES"
        }

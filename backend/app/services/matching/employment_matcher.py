from typing import Dict, Any
from app.models.profile import UserProfile
from app.models.job import Job


class EmploymentMatcher:
    """
    Employment Type Matcher (FULL_TIME, CONTRACT, INTERNSHIP, etc.).
    """

    @staticmethod
    def evaluate(profile: UserProfile, job: Job) -> Dict[str, Any]:
        pref = profile.job_preference
        allowed_types = [t.upper() for t in (pref.employment_types or ["FULL_TIME"])] if pref else ["FULL_TIME"]

        job_type = (job.employment_type or "UNKNOWN").upper()

        if job_type == "UNKNOWN":
            return {"score": 75.0, "confidence": 0.5, "match_reason": "Job employment type is unspecified."}

        if job_type in allowed_types:
            return {"score": 100.0, "confidence": 1.0, "match_reason": f"Employment type '{job_type}' matches candidate preference."}

        return {"score": 30.0, "confidence": 0.9, "match_reason": f"Employment type '{job_type}' differs from allowed preferences {allowed_types}."}

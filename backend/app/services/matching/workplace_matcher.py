from typing import Dict, Any
from app.models.profile import UserProfile
from app.models.job import Job


class WorkplaceMatcher:
    """
    Workplace Arrangement Matcher (REMOTE, HYBRID, ONSITE).
    Does not automatically reject jobs with UNKNOWN workplace type.
    """

    @staticmethod
    def evaluate(profile: UserProfile, job: Job) -> Dict[str, Any]:
        pref = profile.job_preference
        allowed_arrangements = [w.upper() for w in (pref.work_arrangements or ["REMOTE", "HYBRID", "ONSITE"])] if pref else ["REMOTE", "HYBRID", "ONSITE"]

        job_workplace = (job.workplace_type or "UNKNOWN").upper()

        if job_workplace == "UNKNOWN":
            return {"score": 70.0, "confidence": 0.5, "match_reason": "Workplace arrangement unspecified in job listing."}

        if job_workplace in allowed_arrangements:
            return {"score": 100.0, "confidence": 1.0, "match_reason": f"Workplace arrangement '{job_workplace}' matches candidate preference."}

        return {"score": 25.0, "confidence": 0.9, "match_reason": f"Workplace arrangement '{job_workplace}' differs from preferred arrangements {allowed_arrangements}."}

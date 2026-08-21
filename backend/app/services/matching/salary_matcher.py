from typing import Dict, Any
from app.models.profile import UserProfile
from app.models.job import Job


class SalaryMatcher:
    """
    Salary Compatibility Matcher.
    If job has no salary: returns score=100.0, confidence=0.5 (no rejection penalty).
    """

    @staticmethod
    def evaluate(profile: UserProfile, job: Job) -> Dict[str, Any]:
        pref = profile.job_preference
        user_min = pref.min_expected_salary if (pref and pref.min_expected_salary) else None
        user_max = pref.max_expected_salary if (pref and pref.max_expected_salary) else None

        job_min = job.salary_min
        job_max = job.salary_max

        # Missing salary in job listing
        if job_min is None and job_max is None:
            return {"score": 100.0, "confidence": 0.5, "salary_match_status": "UNKNOWN", "match_reason": "Salary not specified in job posting (no penalty applied)."}

        # Missing candidate expectation
        if user_min is None and user_max is None:
            return {"score": 100.0, "confidence": 0.8, "salary_match_status": "UNKNOWN", "match_reason": "Candidate has not specified salary expectations."}

        # Check currency safety
        user_curr = (pref.salary_currency or "USD").upper() if pref else "USD"
        job_curr = (job.salary_currency or "USD").upper()
        if user_curr != job_curr:
            return {
                "score": 80.0,
                "confidence": 0.5,
                "salary_match_status": "UNKNOWN_CURRENCY_MISMATCH",
                "match_reason": f"Currency mismatch ({job_curr} vs {user_curr}). Automated conversion omitted.",
            }

        effective_job_max = job_max or job_min
        effective_job_min = job_min or job_max

        if user_min and effective_job_max < user_min:
            return {
                "score": 0.0,
                "confidence": 1.0,
                "salary_match_status": "BELOW_EXPECTATION",
                "match_reason": f"Job salary max (${effective_job_max}) is below candidate minimum expectation (${user_min}).",
            }

        return {
            "score": 100.0,
            "confidence": 1.0,
            "salary_match_status": "MATCH",
            "match_reason": f"Job salary range (${effective_job_min} - ${effective_job_max}) aligns with candidate expectations.",
        }

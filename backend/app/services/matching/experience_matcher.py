from typing import Dict, Any
from app.models.profile import UserProfile
from app.models.job import Job


class ExperienceMatcher:
    """
    Experience Bounds Matcher.
    Evaluates candidate years_of_experience against job min/max requirements.
    """

    @staticmethod
    def evaluate(profile: UserProfile, job: Job) -> Dict[str, Any]:
        user_exp = float(profile.years_of_experience or 0.0)
        job_min = job.experience_min
        job_max = job.experience_max

        # Missing experience requirement in job
        if job_min is None and job_max is None:
            return {"score": 100.0, "confidence": 0.6, "match_reason": "Job experience requirements unspecified."}

        # Fresher check
        desc_lower = (job.description or "").lower()
        if user_exp == 0 and ("fresher" in desc_lower or "entry level" in desc_lower):
            return {"score": 100.0, "confidence": 1.0, "match_reason": "Job explicitly accepts freshers / entry level candidates."}

        if job_min is not None and user_exp < job_min:
            diff = job_min - user_exp
            score = max(0.0, 100.0 - (diff * 35.0))
            return {
                "score": round(score, 2),
                "confidence": 0.9,
                "match_reason": f"Candidate experience ({user_exp} yrs) is below job minimum ({job_min} yrs).",
            }

        if job_max is not None and user_exp > job_max:
            return {
                "score": 85.0,
                "confidence": 0.8,
                "match_reason": f"Candidate experience ({user_exp} yrs) exceeds job maximum ({job_max} yrs).",
            }

        return {"score": 100.0, "confidence": 1.0, "match_reason": f"Candidate experience ({user_exp} yrs) meets job requirement ({job_min or 0} - {job_max or 'N/A'} yrs)."}

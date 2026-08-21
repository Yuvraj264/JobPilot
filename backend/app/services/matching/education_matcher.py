from typing import Dict, Any
from app.models.profile import UserProfile
from app.models.job import Job


class EducationMatcher:
    """
    Education Qualification Matcher.
    If requirement is ambiguous, returns UNKNOWN without rejecting.
    """

    @staticmethod
    def evaluate(profile: UserProfile, job: Job) -> Dict[str, Any]:
        desc_lower = (job.description or "").lower()
        title_lower = job.title.lower()

        # Check if degree is mentioned in job
        degrees = ["bachelor", "b.tech", "b.e.", "b.s.", "master", "m.tech", "m.s.", "phd"]
        job_req_degrees = [d for d in degrees if d in desc_lower or d in title_lower]

        if not job_req_degrees:
            return {"score": 100.0, "confidence": 0.5, "match_reason": "No explicit education degree requirements detected in job posting."}

        profile_degrees = [e.degree.lower() for e in (profile.education or []) if e.degree]
        if not profile_degrees:
            return {"score": 75.0, "confidence": 0.6, "match_reason": "Job requests specific degree, but profile education list is unpopulated."}

        for req in job_req_degrees:
            for cand_deg in profile_degrees:
                if req in cand_deg or cand_deg in req:
                    return {"score": 100.0, "confidence": 1.0, "match_reason": f"Candidate degree '{cand_deg}' matches job requirement '{req}'."}

        return {"score": 70.0, "confidence": 0.7, "match_reason": f"Job requests degree ({job_req_degrees}), candidate lists ({profile_degrees})."}

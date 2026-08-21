from typing import Dict, Any
from app.models.profile import UserProfile
from app.models.job import Job
from app.services.normalization.location_normalizer import LocationNormalizer


class LocationMatcher:
    """
    Location Compatibility Matcher.
    Evaluates city equivalences (Bangalore == Bengaluru), remote preferences, and relocation status.
    """

    @staticmethod
    def evaluate(profile: UserProfile, job: Job) -> Dict[str, Any]:
        pref = profile.job_preference
        job_loc = job.normalized_location or job.location or ""
        
        # If job is Remote and user accepts remote/hybrid
        if job.workplace_type == "REMOTE" or "remote" in job_loc.lower():
            if not pref or "REMOTE" in (pref.work_arrangements or ["REMOTE"]):
                return {"score": 100.0, "confidence": 1.0, "match_reason": "Job is Remote matching candidate preference."}

        preferred_locations = [loc.lower() for loc in (pref.preferred_locations or [])] if pref else []
        if not preferred_locations:
            if profile.current_city:
                preferred_locations.append(profile.current_city.lower())

        if not preferred_locations:
            return {"score": 80.0, "confidence": 0.5, "match_reason": "No candidate location preference specified."}

        # Check exact or normalized city equivalence
        clean_job_loc, std_job_loc = LocationNormalizer.normalize(job_loc)
        std_job_loc_lower = (std_job_loc or "").lower()

        for pref_loc in preferred_locations:
            clean_pref_loc, std_pref_loc = LocationNormalizer.normalize(pref_loc)
            std_pref_loc_lower = (std_pref_loc or "").lower()

            if std_pref_loc_lower and std_pref_loc_lower in std_job_loc_lower:
                return {"score": 100.0, "confidence": 1.0, "match_reason": f"Location '{job_loc}' matches preferred location '{pref_loc}'."}
            if pref_loc in job_loc.lower() or job_loc.lower() in pref_loc:
                return {"score": 90.0, "confidence": 0.9, "match_reason": f"Partial location match between '{job_loc}' and '{pref_loc}'."}

        # Candidate relocation status
        if pref and pref.relocation_status:
            return {"score": 70.0, "confidence": 0.8, "match_reason": "Location differs, but candidate is open to relocation."}

        return {"score": 20.0, "confidence": 0.9, "match_reason": f"Job location '{job_loc}' does not match preferred locations {preferred_locations}."}

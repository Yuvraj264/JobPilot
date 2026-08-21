from typing import Dict, List, Any
from app.models.profile import UserProfile
from app.models.job import Job


class EligibilityEngine:
    """
    Eligibility Engine evaluating hard requirements vs soft preferences.
    Hard failures trigger eligible=False and force SKIP recommendation.
    """

    @staticmethod
    def evaluate(profile: UserProfile, job: Job) -> Dict[str, Any]:
        hard_failures: List[str] = []
        warnings: List[str] = []

        user_exp = float(profile.years_of_experience or 0.0)
        pref = profile.job_preference

        # 1. Experience Check (Hard Failure if candidate has significantly less experience than required)
        if job.experience_min is not None and job.experience_min > 0:
            if user_exp < (job.experience_min - 0.5):
                # Check if job explicitly mentions "freshers welcome" or "entry level"
                desc_lower = (job.description or "").lower()
                if "fresher" not in desc_lower and "entry level" not in desc_lower:
                    hard_failures.append(
                        f"Experience Mismatch: Job requires minimum {job.experience_min} years, but candidate profile lists {user_exp} years."
                    )

        # 2. Work Authorization / Sponsorship Check
        if pref:
            if pref.authorized_to_work is False:
                hard_failures.append("Work Authorization: Profile indicates candidate is not authorized to work in target country.")
            if pref.requires_sponsorship:
                desc_lower = (job.description or "").lower()
                if "no sponsorship" in desc_lower or "cannot sponsor" in desc_lower:
                    hard_failures.append("Sponsorship Conflict: Job description explicitly prohibits visa sponsorship.")

        # 3. Location & Relocation Constraint Check (Hard failure only for Onsite jobs with zero location match & no relocation)
        if pref and job.workplace_type == "ONSITE" and job.location:
            job_loc_lower = job.location.lower()
            pref_locs = [loc.lower() for loc in (pref.preferred_locations or [])]
            
            # Check if any preferred location is in job location
            loc_matched = any(p in job_loc_lower for p in pref_locs) if pref_locs else True
            if not loc_matched and not pref.relocation_status:
                hard_failures.append(
                    f"Location Constraint: Job is Onsite at '{job.location}' which is not in candidate preferred locations, and relocation is declined."
                )

        # Soft Warnings
        if job.experience_max is not None and user_exp > (job.experience_max + 3.0):
            warnings.append(f"Overqualification Notice: Candidate experience ({user_exp} yrs) exceeds job maximum ({job.experience_max} yrs).")

        eligible = len(hard_failures) == 0
        return {
            "eligible": eligible,
            "hard_failures": hard_failures,
            "warnings": warnings,
        }

from typing import Dict, Any, List
from app.models.profile import UserProfile
from app.models.job import Job
from app.services.matching.skill_matcher import SkillMatcher

class SkillGapAnalyzer:
    """
    Skill Gap Analyzer comparing job requirements to user profile skills.
    Provides actionable missing skill details without fabricating resume experience.
    """

    @staticmethod
    def analyze(profile: UserProfile, job: Job) -> Dict[str, Any]:
        # Extract skills from job description
        job_skills = SkillMatcher.extract_job_skills(job)
        required_req = job_skills.get("required", [])
        preferred_req = job_skills.get("preferred", [])

        # Map profile skills
        profile_skills_map = {}
        for s in (profile.skills or []):
            norm_name = SkillMatcher.normalize_skill_name(s.name).lower()
            profile_skills_map[norm_name] = s

        required_gap = {}
        for skill in required_req:
            norm_skill = skill.lower()
            if norm_skill in profile_skills_map:
                profile_skill = profile_skills_map[norm_skill]
                exp = profile_skill.years_of_experience or 0.0
                prof = (profile_skill.proficiency or "").lower()
                if exp >= 3.0 or prof in ["expert", "advanced", "lead", "senior"]:
                    required_gap[skill] = "STRONG"
                else:
                    required_gap[skill] = "PARTIAL"
            else:
                required_gap[skill] = "MISSING"

        preferred_gap = {}
        for skill in preferred_req:
            norm_skill = skill.lower()
            if norm_skill in profile_skills_map:
                profile_skill = profile_skills_map[norm_skill]
                exp = profile_skill.years_of_experience or 0.0
                prof = (profile_skill.proficiency or "").lower()
                if exp >= 3.0 or prof in ["expert", "advanced", "lead", "senior"]:
                    preferred_gap[skill] = "STRONG"
                else:
                    preferred_gap[skill] = "PARTIAL"
            else:
                preferred_gap[skill] = "MISSING"

        return {
            "required": required_gap,
            "preferred": preferred_gap,
        }

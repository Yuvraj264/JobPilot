import re
from typing import Dict, List, Any
from app.models.profile import UserProfile
from app.models.job import Job
from app.services.parser.deterministic_parser import DeterministicParser, COMMON_SKILLS

SKILL_SYNONYMS = {
    "js": "JavaScript",
    "ts": "TypeScript",
    "py": "Python",
    "postgres": "PostgreSQL",
    "postgres sql": "PostgreSQL",
    "qa": "Manual Testing",
    "testing": "Manual Testing",
    "reactjs": "React",
    "nodejs": "Node.js",
    "aws cloud": "AWS",
}


class SkillMatcher:
    """
    Skill Extraction & Matching Engine.
    Extracted skills from Job are matched against Profile skills.
    Returns match percentage, matched skills, and missing required/preferred skills.
    """

    @staticmethod
    def normalize_skill_name(raw_skill: str) -> str:
        cleaned = raw_skill.strip().lower()
        if cleaned in SKILL_SYNONYMS:
            return SKILL_SYNONYMS[cleaned]
        for canonical_cat, skill_list in COMMON_SKILLS.items():
            for s in skill_list:
                if s.lower() == cleaned:
                    return s
        return raw_skill.strip()

    @staticmethod
    def extract_job_skills(job: Job) -> Dict[str, List[str]]:
        desc_text = job.description or ""
        title_lower = job.title.lower()
        desc_lower = desc_text.lower()

        pref_index = -1
        for pref_kw in ["preferred:", "preferred skills:", "nice to have:", "bonus:"]:
            idx = desc_lower.find(pref_kw)
            if idx != -1:
                pref_index = idx
                break

        required_text = desc_text if pref_index == -1 else desc_text[:pref_index]
        preferred_text = "" if pref_index == -1 else desc_text[pref_index:]

        req_extracted = DeterministicParser.extract_skills(f"{job.title}\n{required_text}")
        pref_extracted = DeterministicParser.extract_skills(preferred_text) if preferred_text else []

        required: List[str] = []
        preferred: List[str] = []

        for item in req_extracted:
            s_name = SkillMatcher.normalize_skill_name(item["name"])
            if s_name not in required:
                required.append(s_name)

        for item in pref_extracted:
            s_name = SkillMatcher.normalize_skill_name(item["name"])
            if s_name not in required and s_name not in preferred:
                preferred.append(s_name)

        return {
            "required": required,
            "preferred": preferred,
        }

    @staticmethod
    def evaluate(profile: UserProfile, job: Job) -> Dict[str, Any]:
        job_skills = SkillMatcher.extract_job_skills(job)
        required_req = job_skills["required"]
        preferred_req = job_skills["preferred"]

        profile_skills_map = {
            SkillMatcher.normalize_skill_name(s.name).lower(): s.name
            for s in (profile.skills or [])
        }

        matched_required: List[str] = []
        missing_required: List[str] = []
        for req in required_req:
            if req.lower() in profile_skills_map:
                matched_required.append(req)
            else:
                missing_required.append(req)

        matched_preferred: List[str] = []
        missing_preferred: List[str] = []
        for pref in preferred_req:
            if pref.lower() in profile_skills_map:
                matched_preferred.append(pref)
            else:
                missing_preferred.append(pref)

        req_score = (len(matched_required) / len(required_req) * 100.0) if required_req else 100.0
        pref_score = (len(matched_preferred) / len(preferred_req) * 100.0) if preferred_req else 100.0

        # Overall Skill Score: 80% weight on required, 20% weight on preferred
        if required_req and preferred_req:
            overall_skill_score = (req_score * 0.8) + (pref_score * 0.2)
        else:
            overall_skill_score = req_score

        return {
            "score": round(overall_skill_score, 2),
            "required_match_pct": round(req_score, 2),
            "preferred_match_pct": round(pref_score, 2),
            "matched_skills": matched_required + matched_preferred,
            "missing_required": missing_required,
            "missing_preferred": missing_preferred,
        }

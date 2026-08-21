import re
from typing import Dict, List, Any
from app.models.profile import UserProfile
from app.models.job import Job

# Compact Role Taxonomy & Broad Role Family Mapping
ROLE_FAMILIES = {
    "qa_testing": [
        "qa engineer", "software test engineer", "quality assurance engineer",
        "sdet", "qa automation engineer", "test automation engineer", "qa tester", "tester"
    ],
    "backend_dev": [
        "python developer", "backend engineer", "python backend engineer",
        "software engineer", "full stack developer", "backend developer", "python engineer"
    ],
    "frontend_dev": [
        "frontend engineer", "frontend developer", "react developer", "ui engineer", "web developer"
    ],
    "devops_cloud": [
        "devops engineer", "cloud engineer", "site reliability engineer", "sre", "infrastructure engineer"
    ],
    "data_analytics": [
        "data analyst", "data engineer", "data scientist", "business intelligence analyst", "bi analyst"
    ]
}


class RoleMatcher:
    """
    Role Similarity Matcher.
    Compares target roles in JobPreference against Job Title using role family taxonomy and fuzzy substring heuristics.
    """

    @staticmethod
    def evaluate(profile: UserProfile, job: Job) -> Dict[str, Any]:
        target_roles = []
        if profile.job_preference and profile.job_preference.target_roles:
            target_roles = [r.strip().lower() for r in profile.job_preference.target_roles]
        
        if not target_roles and profile.current_role:
            target_roles = [profile.current_role.strip().lower()]

        if not target_roles:
            return {"score": 75.0, "confidence": 0.5, "role_match_type": "DEFAULT_UNKNOWN"}

        job_title_lower = job.title.strip().lower()

        # 1. Exact string match
        for target in target_roles:
            if target == job_title_lower:
                return {"score": 100.0, "confidence": 1.0, "role_match_type": "EXACT", "matched_role": target}

        # 2. Substring / Word Match
        for target in target_roles:
            if target in job_title_lower or job_title_lower in target:
                return {"score": 90.0, "confidence": 0.9, "role_match_type": "SUBSTRING", "matched_role": target}

        # 3. Role Family Taxonomy Match
        for family_name, keywords in ROLE_FAMILIES.items():
            job_in_family = any(kw in job_title_lower for kw in keywords)
            if job_in_family:
                for target in target_roles:
                    target_in_family = any(kw in target for kw in keywords)
                    if target_in_family:
                        return {
                            "score": 85.0,
                            "confidence": 0.85,
                            "role_match_type": "ROLE_FAMILY",
                            "family": family_name,
                            "matched_role": target,
                        }

        # 4. Partial Fallback Match
        for target in target_roles:
            words = [w for w in target.split() if len(w) > 2]
            matched_words = [w for w in words if w in job_title_lower]
            if matched_words:
                match_ratio = len(matched_words) / len(words)
                return {
                    "score": round(60.0 + (match_ratio * 25.0), 2),
                    "confidence": 0.7,
                    "role_match_type": "PARTIAL_WORD",
                    "matched_role": target,
                }

        return {"score": 40.0, "confidence": 0.8, "role_match_type": "UNRELATED"}

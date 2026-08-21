from typing import Dict, List, Any
from app.models.profile import UserProfile
from app.models.resume import Resume


class ConsistencyService:
    """
    Deterministic Consistency Checker.
    Compares canonical User Profile (Phase 2) against Parsed Resume (Phase 3).
    Detects mismatches without modifying either source.
    """

    @staticmethod
    def check_consistency(profile: UserProfile, resume: Resume) -> Dict[str, Any]:
        issues: List[Dict[str, str]] = []

        if not profile or not resume:
            return {"status": "warning", "issues": [{"type": "MISSING_DATA", "message": "Profile or resume data unavailable for consistency comparison."}]}

        # 1. Skill Mismatch Analysis
        profile_skills = {s.name.lower() for s in profile.skills} if profile.skills else set()
        resume_skills = {s.name.lower() for s in resume.skills} if resume.skills else set()

        for ps in profile.skills or []:
            if ps.name.lower() not in resume_skills:
                issues.append({
                    "type": "SKILL_MISSING_FROM_RESUME",
                    "message": f"Skill '{ps.name}' exists in your User Profile but is missing from this resume."
                })

        for rs in resume.skills or []:
            if rs.name.lower() not in profile_skills:
                issues.append({
                    "type": "RESUME_SKILL_MISSING_FROM_PROFILE",
                    "message": f"Skill '{rs.name}' was extracted from this resume but is not listed in your User Profile."
                })

        # 2. Education Mismatch Analysis
        profile_degrees = {e.degree.lower() for e in profile.education if e.degree} if profile.education else set()
        for re_edu in resume.education or []:
            if re_edu.degree and re_edu.degree.lower() not in profile_degrees:
                issues.append({
                    "type": "EDUCATION_MISMATCH",
                    "message": f"Education qualification '{re_edu.degree}' ({re_edu.institution}) in resume is not found in your User Profile."
                })

        # 3. Project Mismatch Analysis
        profile_projects = {p.name.lower() for p in profile.projects if p.name} if profile.projects else set()
        for rp in resume.projects or []:
            if rp.name and rp.name.lower() not in profile_projects:
                issues.append({
                    "type": "PROJECT_MISMATCH",
                    "message": f"Project '{rp.name}' listed in resume is missing from your User Profile."
                })

        # 4. Contact Information Check
        if profile.email and profile.email.lower() not in resume.original_filename.lower():
            pass  # Normal

        status = "warning" if len(issues) > 0 else "ok"
        return {
            "status": status,
            "issues": issues,
            "total_issues": len(issues),
        }

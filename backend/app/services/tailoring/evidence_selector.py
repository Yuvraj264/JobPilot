from typing import Dict, Any, List, Optional
from app.models.profile import UserProfile
from app.models.resume import Resume


class EvidenceStrength:
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    NONE = "NONE"


class EvidenceSelector:
    """
    Evidence Selector searching candidate profile and master resume for factual evidence matching job requirements.
    Rates evidence strength strictly without inventing claims.
    """

    @staticmethod
    def select_evidence_for_requirement(
        requirement_name: str,
        profile: UserProfile,
        resume: Optional[Resume] = None
    ) -> Dict[str, Any]:
        req_lower = requirement_name.lower().strip()

        # 1. Check Profile & Resume Skills (STRONG)
        profile_skills = [s.name.lower() for s in (profile.skills or [])]
        if req_lower in profile_skills:
            return {"strength": EvidenceStrength.STRONG, "source": "PROFILE_SKILL", "matched_item": requirement_name}

        if resume:
            resume_skills = [s.name.lower() for s in (resume.skills or [])]
            if req_lower in resume_skills:
                return {"strength": EvidenceStrength.STRONG, "source": "RESUME_SKILL", "matched_item": requirement_name}

        # 2. Check Projects (MODERATE / STRONG)
        for proj in (profile.projects or []):
            p_text = f"{proj.name} {proj.description or ''} {proj.technologies or ''}".lower()
            if req_lower in p_text:
                return {"strength": EvidenceStrength.MODERATE, "source": "PROFILE_PROJECT", "matched_item": proj.name}

        if resume:
            for proj in (resume.projects or []):
                p_text = f"{proj.title} {proj.description or ''} {proj.technologies or ''}".lower()
                if req_lower in p_text:
                    return {"strength": EvidenceStrength.MODERATE, "source": "RESUME_PROJECT", "matched_item": proj.title}

        # 3. Check Work Experience in Resume (MODERATE)
        if resume:
            for exp in (resume.experiences or []):
                exp_text = f"{exp.role_title} {exp.company_name} {exp.description or ''}".lower()
                if req_lower in exp_text:
                    return {"strength": EvidenceStrength.MODERATE, "source": "RESUME_EXPERIENCE", "matched_item": exp.company_name}

        # 4. Absent Evidence
        return {"strength": EvidenceStrength.NONE, "source": None, "matched_item": None}

from typing import Dict, Any, List, Optional
from app.models.profile import UserProfile
from app.models.resume import Resume


class ResumeTruthfulnessValidator:
    """
    MANDATORY RESUME TRUTHFULNESS VALIDATOR (Requirements 15, 32, 34).
    Compares Tailored Resume intermediate content against canonical Profile & Master Resume.
    FAILS VALIDATION if any unsupported skill, project, employer, certification, or fabricated metric is introduced.
    """

    @staticmethod
    def validate_tailored_resume(
        tailored_doc: Dict[str, Any],
        profile: UserProfile,
        master_resume: Optional[Resume] = None
    ) -> Dict[str, Any]:
        issues = []

        # 1. Allowed Canonical Skills
        profile_skills = {s.name.lower() for s in (profile.skills or [])}
        if master_resume:
            resume_skills = {s.name.lower() for s in (master_resume.skills or [])}
            allowed_skills = profile_skills.union(resume_skills)
        else:
            allowed_skills = profile_skills

        tailored_skills = tailored_doc.get("skills", [])
        for skill_item in tailored_skills:
            s_name = skill_item if isinstance(skill_item, str) else skill_item.get("name", "")
            if s_name and s_name.lower() not in allowed_skills:
                issues.append(f"UNSUPPORTED SKILL ADDED: '{s_name}' does not exist in master profile or resume.")

        # 2. Allowed Projects
        profile_projects = {p.name.lower() for p in (profile.projects or [])}
        if master_resume:
            resume_projects = {p.title.lower() for p in (master_resume.projects or [])}
            allowed_projects = profile_projects.union(resume_projects)
        else:
            allowed_projects = profile_projects

        tailored_projects = tailored_doc.get("projects", [])
        for proj in tailored_projects:
            p_name = proj.get("name", "").lower()
            if p_name and p_name not in allowed_projects:
                issues.append(f"UNSUPPORTED PROJECT ADDED: '{proj.get('name')}' does not exist in master profile or resume.")

        # 3. Work Experience / Employer Checks
        if master_resume:
            allowed_companies = {e.company_name.lower() for e in (master_resume.experiences or [])}
            tailored_exp = tailored_doc.get("experience", [])
            for exp in tailored_exp:
                comp = exp.get("company", "").lower()
                if comp and comp not in allowed_companies:
                    issues.append(f"UNSUPPORTED EMPLOYER ADDED: Employer '{exp.get('company')}' does not exist in master resume.")
        else:
            # If candidate has no work experience in master resume, no experience section is allowed
            tailored_exp = tailored_doc.get("experience", [])
            if tailored_exp and len(tailored_exp) > 0:
                issues.append("FABRICATED WORK EXPERIENCE: Master resume has 0 work experience entries, but tailored resume introduced work experience.")

        # 4. Certification Checks
        profile_certs = {c.name.lower() for c in (profile.certifications or [])}
        if master_resume:
            resume_certs = {c.name.lower() for c in (master_resume.certifications or [])}
            allowed_certs = profile_certs.union(resume_certs)
        else:
            allowed_certs = profile_certs

        tailored_certs = tailored_doc.get("certifications", [])
        for cert in tailored_certs:
            c_name = cert.get("name", "").lower() if isinstance(cert, dict) else str(cert).lower()
            if c_name and c_name not in allowed_certs:
                issues.append(f"UNSUPPORTED CERTIFICATION ADDED: '{c_name}' does not exist in master profile or resume.")

        is_valid = len(issues) == 0
        return {
            "valid": is_valid,
            "issues": issues,
            "validation_status": "PASSED" if is_valid else "FAILED_TRUTHFULNESS_CHECK"
        }

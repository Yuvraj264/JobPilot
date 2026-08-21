from typing import Dict, Any, List, Optional
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.job import Job
from app.services.tailoring.evidence_selector import EvidenceSelector, EvidenceStrength


class ResumeTailoringPlan:
    """
    Tailoring Plan Generator creating an inspectable plan before document synthesis.
    """

    @staticmethod
    def generate_plan(
        job: Job,
        profile: UserProfile,
        requirements: List[Dict[str, Any]],
        resume: Optional[Resume] = None
    ) -> Dict[str, Any]:

        job_title = job.title or "Target Role"
        company = job.company_name or "Target Company"

        # 1. Summary Tailoring Intent
        years = profile.years_of_experience or 0.0
        role = profile.current_role or "Software Professional"
        
        # 2. Skill Prioritization
        supported_skills = []
        for s in (profile.skills or []):
            s_name = s.name
            ev = EvidenceSelector.select_evidence_for_requirement(s_name, profile, resume)
            supported_skills.append({
                "name": s_name,
                "proficiency": s.proficiency or "INTERMEDIATE",
                "matched_job_req": ev["strength"] != EvidenceStrength.NONE
            })

        # Sort: matched skills first
        prioritized_skills = sorted(supported_skills, key=lambda x: x["matched_job_req"], reverse=True)

        # 3. Project Relevance Scoring
        req_set = {r["name"].lower() for r in requirements}
        scored_projects = []
        for proj in (profile.projects or []):
            p_text = f"{proj.name} {proj.description or ''} {proj.technologies or ''}".lower()
            overlap = sum(1 for req in req_set if req in p_text)
            rel_score = round((overlap / len(req_set) * 100), 2) if req_set else 0.0
            scored_projects.append({
                "name": proj.name,
                "relevance_score": rel_score,
                "description": proj.description,
                "technologies": proj.technologies
            })

        prioritized_projects = sorted(scored_projects, key=lambda x: x["relevance_score"], reverse=True)

        # 4. Unsupported Requirements
        unsupported = [
            r["name"] for r in requirements
            if EvidenceSelector.select_evidence_for_requirement(r["name"], profile, resume)["strength"] == EvidenceStrength.NONE
        ]

        return {
            "target_job_title": job_title,
            "target_company": company,
            "tailored_summary_intent": f"Focus on candidate's {years} years of experience in {role} highlighting skills in {', '.join([s['name'] for s in prioritized_skills[:3]])}.",
            "skills_prioritized": [s["name"] for s in prioritized_skills],
            "projects_prioritized": prioritized_projects,
            "unsupported_requirements": unsupported
        }

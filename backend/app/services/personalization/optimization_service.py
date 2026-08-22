from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.personalization import (
    OptimizationCycle,
    OptimizationSuggestion,
    ResumeFeedback,
    OutcomeFeedback,
    JobFeedback,
    PersonalPreferenceProfile
)
from app.models.profile import UserProfile, Skill, Project, Certification
from app.models.resume import Resume
from app.models.job import Job
from app.models.application import Application


class OptimizationSuggestionService:
    """
    Business layer for identifying missing skills, evaluating variant analytics,
    verifying skill evidence, and logging continuous weekly optimization cycles.
    """

    @classmethod
    def get_skill_evidence(cls, db: Session, profile_id: int, skill_name: str) -> Dict[str, Any]:
        """
        Determines evidence supporting a skill from profile, resume, projects, and certifications.
        Never infers skill possession from job requirements.
        """
        sources = []
        details = []
        name_lower = skill_name.lower().strip()

        # 1. Check profile skills
        profile_skills = db.query(Skill).filter(
            Skill.profile_id == profile_id,
            func.lower(Skill.name) == name_lower
        ).all()
        if profile_skills:
            sources.append("USER_PROFILE")
            for s in profile_skills:
                details.append(f"Listed in Profile skills with {s.proficiency or 'Unspecified'} proficiency.")

        # 2. Check Resumes
        resumes = db.query(Resume).filter(Resume.profile_id == profile_id).all()
        for r in resumes:
            # We can check if name is in parsed_skills or resume text
            raw_content = (r.extracted_text or "").lower()
            if name_lower in raw_content:
                sources.append("RESUME")
                details.append(f"Found in text of Resume: '{r.filename}'.")
                break

        # 3. Check Projects
        projects = db.query(Project).filter(Project.profile_id == profile_id).all()
        for p in projects:
            p_tech = [t.lower().strip() for t in (p.technologies or [])]
            if name_lower in p_tech or name_lower in (p.description or "").lower():
                sources.append("PROJECT")
                details.append(f"Found in Project: '{p.name}'.")
                break

        # 4. Check Certifications
        certs = db.query(Certification).filter(Certification.profile_id == profile_id).all()
        for c in certs:
            if name_lower in (c.name or "").lower():
                sources.append("CERTIFICATION")
                details.append(f"Found in Certification: '{c.name}' issued by {c.issuing_organization}.")
                break

        supported = len(sources) > 0
        return {
            "skill": skill_name,
            "supported": supported,
            "sources": list(set(sources)),
            "details": details
        }

    @classmethod
    def run_weekly_optimization(cls, db: Session, profile_id: int) -> OptimizationCycle:
        """
        Runs weekly feedback and recommendation analytics to identify missing skills,
        variant performance, and generate suggestions.
        """
        # Calculate start/end of the current period
        now = datetime.utcnow()
        start_date = now - timedelta(days=7)
        period_str = now.strftime("%Y-W%U")

        # 1. Gather metrics
        total_apps = db.query(Application).filter(
            Application.profile_id == profile_id,
            Application.created_at >= start_date
        ).count()

        outcomes = db.query(OutcomeFeedback).filter(
            OutcomeFeedback.profile_id == profile_id,
            OutcomeFeedback.created_at >= start_date
        ).all()
        outcome_counts = {}
        for o in outcomes:
            outcome_counts[o.outcome] = outcome_counts.get(o.outcome, 0) + 1

        # 2. Identify missing skills
        # Find all saved jobs in the last week
        saved_jobs = db.query(Job).join(JobFeedback).filter(
            JobFeedback.profile_id == profile_id,
            JobFeedback.feedback_type == "Save",
            JobFeedback.created_at >= start_date
        ).all()

        missing_skills_map = {}
        for job in saved_jobs:
            req_skills = job.source_metadata.get("required_skills", []) if job.source_metadata else []
            for s in req_skills:
                evidence = cls.get_skill_evidence(db, profile_id, s)
                if not evidence["supported"]:
                    missing_skills_map[s] = missing_skills_map.get(s, 0) + 1

        # Top missing skills
        sorted_gaps = sorted(missing_skills_map.items(), key=lambda x: x[1], reverse=True)
        suggestions_list = []
        problems_list = []

        if sorted_gaps:
            top_gap, count = sorted_gaps[0]
            problems_list.append(f"Missing skill '{top_gap}' requested frequently in saved jobs.")
            suggestions_list.append(
                f"Consider gaining experience or completing certifications for '{top_gap}'. It appeared in {count} saved jobs this week."
            )

        # 3. Create OptimizationSuggestion records
        for gap, count in sorted_gaps[:2]:
            exists = db.query(OptimizationSuggestion).filter(
                OptimizationSuggestion.profile_id == profile_id,
                OptimizationSuggestion.category == "skill_gap",
                OptimizationSuggestion.suggestion.like(f"%'{gap}'%"),
                OptimizationSuggestion.status == "PENDING"
            ).first()
            if not exists:
                sug = OptimizationSuggestion(
                    profile_id=profile_id,
                    category="skill_gap",
                    suggestion=f"'{gap}' is a common skill gap requested in your saved jobs. Consider adding evidence or learning it.",
                    evidence=f"Appeared in {count} saved listings this week.",
                    severity="MEDIUM",
                    status="PENDING",
                    proposed_changes={
                        "preference_key": "preferred_skills",
                        "action": "flag_gap",
                        "value": gap
                    }
                )
                db.add(sug)

        # 4. Log optimization cycle report
        cycle = OptimizationCycle(
            profile_id=profile_id,
            period=period_str,
            metrics={
                "applications_submitted": total_apps,
                "outcomes": outcome_counts,
                "saved_jobs_analyzed": len(saved_jobs)
            },
            problems=problems_list,
            suggestions=suggestions_list,
            accepted_changes=[],
            rejected_changes=[]
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)
        return cycle

    @classmethod
    def get_resume_variant_analytics(cls, db: Session, profile_id: int) -> List[Dict[str, Any]]:
        """
        Calculates performance analytics for different resume variants.
        """
        resumes = db.query(Resume).filter(Resume.profile_id == profile_id).all()
        analytics = []

        for r in resumes:
            # Count applications using this resume
            apps_count = db.query(Application).filter(
                Application.profile_id == profile_id,
                Application.selected_resume_id == r.id
            ).count()

            # Count interviews for these applications
            interviews = db.query(Application).join(OutcomeFeedback).filter(
                Application.profile_id == profile_id,
                Application.selected_resume_id == r.id,
                OutcomeFeedback.outcome == "Interview"
            ).count()

            # Count offers
            offers = db.query(Application).join(OutcomeFeedback).filter(
                Application.profile_id == profile_id,
                Application.selected_resume_id == r.id,
                OutcomeFeedback.outcome == "Offer"
            ).count()

            analytics.append({
                "resume_id": r.id,
                "filename": r.filename,
                "applications": apps_count,
                "interviews": interviews,
                "offers": offers,
                "interview_rate": round((interviews / apps_count * 100), 2) if apps_count > 0 else 0.0,
                "offer_rate": round((offers / apps_count * 100), 2) if apps_count > 0 else 0.0
            })

        return analytics

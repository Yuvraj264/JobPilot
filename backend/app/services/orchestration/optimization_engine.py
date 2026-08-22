from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.matching import JobMatch
from app.models.profile import UserProfile
from app.models.application import Application, HumanInterventionEvent, SubmissionRun
from app.models.tailoring import TailoredResume
from app.models.screening import ApplicationQuestion, ApplicationAnswer
from app.services.matching.skill_matcher import SkillMatcher

class OptimizationEngine:
    """
    Optimization Engine identifying platform execution issues and profile gaps.
    Generates actionable suggestions to optimize application success rates.
    """

    @staticmethod
    def get_suggestions(db: Session, profile: UserProfile) -> List[Dict[str, Any]]:
        suggestions = []

        # 1. Analyze profile missing skills from failed/reviewed match pools
        matches = db.query(JobMatch).filter(JobMatch.profile_id == profile.id).all()
        user_skills_set = {
            SkillMatcher.normalize_skill_name(s.name).lower()
            for s in (profile.skills or [])
        }
        
        missing_skills_counter = {}
        for m in matches:
            if m.overall_score < 75.0:  # Low matches
                skills = SkillMatcher.extract_job_skills(m.job)
                for s in skills.get("required", []):
                    if s.lower() not in user_skills_set:
                        missing_skills_counter[s] = missing_skills_counter.get(s, 0) + 1

        for skill, count in sorted(missing_skills_counter.items(), key=lambda x: x[1], reverse=True)[:3]:
            suggestions.append({
                "category": "Profile Skill Gap",
                "suggestion": f"Multiple jobs matched have required skill '{skill}', which is missing from your profile. Consider adding it to your profile skills if you have relevant experience.",
                "severity": "HIGH" if count >= 3 else "MEDIUM",
            })

        # 2. Analyze tailored resume keyword coverage
        tailored = db.query(TailoredResume).filter(TailoredResume.profile_id == profile.id).all()
        low_coverage_count = 0
        for t in tailored:
            cov = (t.keyword_analysis or {}).get("coverage", 100.0)
            if cov < 80.0:
                low_coverage_count += 1
        
        if low_coverage_count > 0:
            suggestions.append({
                "category": "Resume Tailoring",
                "suggestion": f"Found {low_coverage_count} tailored resumes with low keyword match coverage (< 80%). Consider reviewing your master resume context to add details for relevant technical keywords.",
                "severity": "MEDIUM",
            })

        # 3. Analyze screening questions/interventions (low confidence)
        questions = db.query(ApplicationQuestion).join(Job).join(JobMatch).filter(JobMatch.profile_id == profile.id).all()
        low_confidence_qs = []
        for q in questions:
            ans = db.query(ApplicationAnswer).filter(ApplicationAnswer.question_id == q.id).first()
            if ans and ans.answer_status == "INSUFFICIENT_INFORMATION":
                low_confidence_qs.append(q.question_text)

        if len(low_confidence_qs) > 0:
            suggestions.append({
                "category": "Screening Questions",
                "suggestion": f"AI was unable to answer {len(low_confidence_qs)} screening questions due to insufficient info (e.g., '{low_confidence_qs[0][:40]}...'). Consider expanding your profile professional summary or project descriptions.",
                "severity": "HIGH",
            })

        # 4. Analyze execution runs/failures
        runs = db.query(SubmissionRun).join(Application).filter(Application.profile_id == profile.id).all()
        failed_runs = [r for r in runs if r.status == "FAILED"]
        if len(failed_runs) > 0:
            suggestions.append({
                "category": "Application Runs",
                "suggestion": f"Detected {len(failed_runs)} failed submission execution runs. Common cause: {failed_runs[0].error_message or 'timeout'}. Consider enabling dry-run or verification steps.",
                "severity": "HIGH",
            })

        # 5. Analyze human intervention events
        interventions = db.query(HumanInterventionEvent).join(Application).filter(Application.profile_id == profile.id).all()
        if len(interventions) > 2:
            suggestions.append({
                "category": "Automation Interventions",
                "suggestion": f"There were {len(interventions)} automated run pauses requiring human intervention. Ensure credentials are valid and enable human-assisted mode for high-difficulty forms.",
                "severity": "MEDIUM",
            })

        # Base suggestion if none generated
        if not suggestions:
            suggestions.append({
                "category": "System Health",
                "suggestion": "No critical optimization recommendations detected. JobPilot pipelines are running at optimal performance parameters.",
                "severity": "INFO",
            })

        return suggestions

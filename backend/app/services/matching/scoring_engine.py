from typing import Dict, Any, List
from app.models.profile import UserProfile
from app.models.job import Job
from app.models.matching import MatchConfig
from app.services.matching.eligibility_engine import EligibilityEngine
from app.services.matching.skill_matcher import SkillMatcher
from app.services.matching.role_matcher import RoleMatcher
from app.services.matching.location_matcher import LocationMatcher
from app.services.matching.employment_matcher import EmploymentMatcher
from app.services.matching.workplace_matcher import WorkplaceMatcher
from app.services.matching.salary_matcher import SalaryMatcher
from app.services.matching.experience_matcher import ExperienceMatcher
from app.services.matching.education_matcher import EducationMatcher
from app.services.matching.semantic_matcher import SemanticMatcher
from app.services.matching.explanation_generator import ExplanationGenerator


class ScoringEngine:
    """
    Weighted Scoring & Recommendation Engine.
    Combines eligibility, component scores, configurable weights, and user thresholds.
    """

    @staticmethod
    def evaluate_job(profile: UserProfile, job: Job, config: MatchConfig) -> Dict[str, Any]:
        # 1. Eligibility Check
        el_res = EligibilityEngine.evaluate(profile, job)

        # 2. Component Evaluations
        skill_res = SkillMatcher.evaluate(profile, job)
        role_res = RoleMatcher.evaluate(profile, job)
        loc_res = LocationMatcher.evaluate(profile, job)
        emp_res = EmploymentMatcher.evaluate(profile, job)
        work_res = WorkplaceMatcher.evaluate(profile, job)
        sal_res = SalaryMatcher.evaluate(profile, job)
        exp_res = ExperienceMatcher.evaluate(profile, job)
        edu_res = EducationMatcher.evaluate(profile, job)
        sem_res = SemanticMatcher.evaluate(profile, job)

        components = {
            "skills": skill_res.get("score", 0.0),
            "role": role_res.get("score", 0.0),
            "experience": exp_res.get("score", 0.0),
            "location": loc_res.get("score", 0.0),
            "workplace": work_res.get("score", 0.0),
            "employment": emp_res.get("score", 0.0),
            "education": edu_res.get("score", 0.0),
            "salary": sal_res.get("score", 0.0),
            "semantic": sem_res.get("score", 0.0),
        }

        # 3. Weighted Score Calculation
        w_skills = config.weight_skills if config and config.weight_skills is not None else 0.35
        w_role = config.weight_role if config and config.weight_role is not None else 0.20
        w_exp = config.weight_experience if config and config.weight_experience is not None else 0.15
        w_loc = config.weight_location if config and config.weight_location is not None else 0.10
        w_work = config.weight_workplace if config and config.weight_workplace is not None else 0.05
        w_emp = config.weight_employment if config and config.weight_employment is not None else 0.05
        w_edu = config.weight_education if config and config.weight_education is not None else 0.05
        w_sem = config.weight_semantic if config and config.weight_semantic is not None else 0.05

        total_weight = w_skills + w_role + w_exp + w_loc + w_work + w_emp + w_edu + w_sem
        if total_weight == 0:
            total_weight = 1.0

        raw_score = (
            (components["skills"] * w_skills) +
            (components["role"] * w_role) +
            (components["experience"] * w_exp) +
            (components["location"] * w_loc) +
            (components["workplace"] * w_work) +
            (components["employment"] * w_emp) +
            (components["education"] * w_edu) +
            (components["semantic"] * w_sem)
        ) / total_weight

        overall_score = round(max(0.0, min(100.0, raw_score)), 2)

        # 4. Confidence Calculation (Weighted Average of component confidences)
        conf_skills = 0.95
        conf_role = role_res.get("confidence", 0.85)
        conf_loc = loc_res.get("confidence", 0.9)
        conf_exp = exp_res.get("confidence", 0.9)
        conf_overall = round(
            (conf_skills * 0.35 + conf_role * 0.25 + conf_loc * 0.2 + conf_exp * 0.2), 2
        )

        # 5. Recommendation Decision
        threshold_apply = config.threshold_apply if config and config.threshold_apply is not None else 85.0
        threshold_review = config.threshold_review if config and config.threshold_review is not None else 70.0

        # User minimum threshold from Phase 2 application preferences
        user_min_threshold = threshold_apply
        if profile.application_preference and profile.application_preference.min_job_match_score is not None:
            user_min_threshold = max(threshold_apply, float(profile.application_preference.min_job_match_score))

        if not el_res["eligible"]:
            recommendation = "SKIP"
        elif overall_score >= user_min_threshold:
            recommendation = "APPLY"
        elif overall_score >= threshold_review:
            recommendation = "REVIEW"
        else:
            recommendation = "SKIP"

        # 6. Explanation Facts Generation
        exp_dict = ExplanationGenerator.generate(
            job_title=job.title,
            company_name=job.company_name,
            overall_score=overall_score,
            recommendation=recommendation,
            eligible=el_res["eligible"],
            hard_failures=el_res["hard_failures"],
            skill_res=skill_res,
            role_res=role_res,
            loc_res=loc_res,
            exp_res=exp_res,
            salary_res=sal_res,
        )

        return {
            "overall_score": overall_score,
            "recommendation": recommendation,
            "eligible": el_res["eligible"],
            "confidence": conf_overall,
            "component_scores": components,
            "hard_failures": el_res["hard_failures"],
            "warnings": el_res["warnings"],
            "strengths": exp_dict["strengths"],
            "concerns": exp_dict["concerns"],
            "explanation": exp_dict,
        }

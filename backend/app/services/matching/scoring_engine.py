from datetime import datetime, timedelta
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
    Integrates Personalization profiles and Job Quality Warning filters.
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

        base_score = round(max(0.0, min(100.0, raw_score)), 2)
        overall_score = base_score

        # Personalization & Quality Adjustments
        pref_profile = getattr(profile, "personal_preference_profile", None)
        personalization_factor = 1.0
        preference_fit_bonus = 0.0
        job_quality_factor = 1.0
        quality_warnings = []

        # Job Quality Detection
        desc_len = len(job.description or "")
        if desc_len < 150:
            quality_warnings.append("JOB_QUALITY_WARNING: Job description is extremely short or incomplete.")
            job_quality_factor *= 0.90
        if not job.company_name or job.company_name.lower() in ["unknown", "na", "n/a", ""]:
            quality_warnings.append("JOB_QUALITY_WARNING: Missing company information.")
            job_quality_factor *= 0.90
        if job.posted_at and (datetime.utcnow() - job.posted_at) > timedelta(days=30):
            quality_warnings.append("JOB_QUALITY_WARNING: Job listing is older than 30 days and may be stale.")
            job_quality_factor *= 0.95

        # Personal Preference Score adjustment
        if pref_profile and pref_profile.enabled:
            title_lower = (job.title or "").lower()
            for r in pref_profile.preferred_roles:
                if r.get("value", "").lower() in title_lower:
                    preference_fit_bonus += 8.0 * r.get("strength", 1.0)
            for r in pref_profile.disliked_roles:
                if r.get("value", "").lower() in title_lower:
                    preference_fit_bonus -= 12.0 * r.get("strength", 1.0)

            desc_lower = (job.description or "").lower()
            for s in pref_profile.preferred_skills:
                if s.get("value", "").lower() in desc_lower:
                    preference_fit_bonus += 3.0 * s.get("strength", 1.0)
            for s in pref_profile.disliked_skills:
                if s.get("value", "").lower() in desc_lower:
                    preference_fit_bonus -= 6.0 * s.get("strength", 1.0)

            work_type = (job.workplace_type or "").upper()
            for wm in pref_profile.workplace_modes:
                val = wm.get("value", "").upper()
                if val == work_type:
                    if wm.get("type") == "disliked":
                        preference_fit_bonus -= 15.0 * wm.get("strength", 1.0)
                    else:
                        preference_fit_bonus += 5.0 * wm.get("strength", 1.0)

            # Limit preference fit adjustment between -30.0 and +30.0
            preference_fit_bonus = max(-30.0, min(30.0, preference_fit_bonus))
            personalization_factor = 1.0 + (preference_fit_bonus / 100.0)

        # Apply factors
        if pref_profile and pref_profile.enabled:
            overall_score = round(max(0.0, min(100.0, base_score * personalization_factor * job_quality_factor)), 2)
        else:
            overall_score = round(max(0.0, min(100.0, base_score * job_quality_factor)), 2)

        # 4. Confidence Calculation
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

        user_min_threshold = threshold_apply
        if profile.application_preference and profile.application_preference.min_job_match_score is not None:
            user_min_threshold = max(threshold_apply, float(profile.application_preference.min_job_match_score))

        # Do not allow personalization to override hard eligibility requirements
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

        # Append personalization to explanation
        exp_dict["base_match"] = base_score
        exp_dict["preference_fit"] = round(preference_fit_bonus, 2)
        exp_dict["job_quality_factor"] = round(job_quality_factor, 2)
        exp_dict["quality_warnings"] = quality_warnings
        exp_dict["personalization_enabled"] = bool(pref_profile.enabled) if pref_profile else False

        total_warnings = list(el_res["warnings"] or []) + quality_warnings

        return {
            "overall_score": overall_score,
            "recommendation": recommendation,
            "eligible": el_res["eligible"],
            "confidence": conf_overall,
            "component_scores": components,
            "hard_failures": el_res["hard_failures"],
            "warnings": total_warnings,
            "strengths": exp_dict["strengths"],
            "concerns": exp_dict["concerns"],
            "explanation": exp_dict,
        }


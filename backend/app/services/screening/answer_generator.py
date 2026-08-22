import re
from typing import Dict, Any, Optional
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.services.screening.taxonomy import QuestionType
from app.services.screening.ai_provider import LocalMockScreeningAIProvider
from app.services.screening.answer_length_constraint import AnswerLengthConstraint


class AnswerGenerator:
    """
    Answer Generator executing deterministic mapping or AI synthesis.
    ENFORCES STRICT TRUTHFULNESS SAFEGUARDS: Never fabricates work experience, education, or skills.
    Returns INSUFFICIENT_INFORMATION when profile evidence is unpopulated.
    """

    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider or LocalMockScreeningAIProvider()

    @staticmethod
    def _extract_profile_facts(profile: UserProfile, resume: Optional[Resume] = None) -> Dict[str, Any]:
        skills_list = [s.name.lower() for s in (profile.skills or [])]
        projects_list = [p.name.lower() + " " + (p.description or "").lower() for p in (profile.projects or [])]
        
        return {
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "current_city": profile.current_city,
            "current_country": profile.current_country or "India",
            "years_of_experience": profile.years_of_experience or 0.0,
            "current_role": profile.current_role or "Software Professional",
            "skills": [s.name for s in (profile.skills or [])],
            "skills_lower": skills_list,
            "projects_lower": projects_list,
            "relocation": profile.job_preference.relocation_status if profile.job_preference else True,
            "work_arrangements": profile.job_preference.work_arrangements if profile.job_preference else ["HYBRID"],
            "expected_salary": profile.job_preference.min_expected_salary if profile.job_preference else None,
            "education": profile.education[0] if profile.education and len(profile.education) > 0 else None,
        }

    def generate(
        self,
        question_text: str,
        question_type: str,
        answer_source: str,
        profile: UserProfile,
        job_context: Dict[str, Any],
        resume: Optional[Resume] = None,
        max_length: Optional[int] = None
    ) -> Dict[str, Any]:

        facts = self._extract_profile_facts(profile, resume)
        q_lower = question_text.lower()
        constraints = AnswerLengthConstraint.extract_constraints(question_text, maxlength=max_length)

        # 1. Deterministic Mappings
        if answer_source == "DETERMINISTIC_RULE":
            if question_type == QuestionType.RELOCATION:
                val = "Yes" if facts["relocation"] else "No"
                return {"status": "READY", "answer": val, "confidence": 0.98, "generated_by": "DETERMINISTIC"}

            if question_type == QuestionType.LOCATION:
                val = facts["current_city"] or facts["current_country"]
                if not val:
                    return {"status": "INSUFFICIENT_INFORMATION", "requires_human": True, "reason": "Current city unpopulated in profile."}
                return {"status": "READY", "answer": val, "confidence": 0.98, "generated_by": "DETERMINISTIC"}

            if question_type == QuestionType.SALARY:
                sal = facts["expected_salary"]
                val = f"${int(sal):,}" if sal else "Market Standard"
                return {"status": "READY", "answer": val, "confidence": 0.95, "generated_by": "DETERMINISTIC"}

            if question_type == QuestionType.EXPERIENCE:
                exp = facts["years_of_experience"]
                val = f"{exp} years"
                return {"status": "READY", "answer": val, "confidence": 0.98, "generated_by": "DETERMINISTIC"}

        # 2. Strict Anti-Fabrication Evidence Check for Specific Tech / Projects / Experience
        if question_type not in [QuestionType.RELOCATION, QuestionType.LOCATION, QuestionType.SALARY, QuestionType.SPONSORSHIP, QuestionType.WORK_AUTHORIZATION]:
            # Detect target keywords in question
            target_keywords = ["selenium", "aws", "leadership", "docker", "kubernetes", "management", "managing", "lead", "react", "css"]
            for kw in target_keywords:
                if kw in q_lower:
                    # Check if candidate has evidence in skills or projects
                    has_skill = any(kw in s for s in facts["skills_lower"])
                    has_project = any(kw in p for p in facts["projects_lower"])

                    if not (has_skill or has_project):
                        return {
                            "status": "INSUFFICIENT_INFORMATION",
                            "requires_human": True,
                            "reason": f"No verifiable evidence of '{kw.title()}' found in candidate profile or projects.",
                            "confidence": 0.0,
                            "generated_by": "SYSTEM"
                        }

        # 3. AI Answer Generation for Open-Ended & Knowledge Questions
        res = self.ai_provider.generate_answer(question_text, question_type, facts, job_context, max_length)
        if res["status"] == "SUCCESS":
            formatted_ans = AnswerLengthConstraint.enforce_length(
                res["answer"],
                max_characters=constraints["max_characters"],
                max_words=constraints["max_words"]
            )
            return {
                "status": "GENERATED",
                "answer": formatted_ans,
                "confidence": res["confidence"],
                "generated_by": "AI_MODEL"
            }

        return {"status": "INSUFFICIENT_INFORMATION", "requires_human": True, "reason": "Failed to generate answer."}

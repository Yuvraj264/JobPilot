from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ScreeningAIProvider(ABC):
    """
    Abstract AI Provider for Screening Question Answer Generation.
    Exposes a unified interface so external LLMs or local models can be swapped without rewriting QuestionEngine.
    """

    @abstractmethod
    def generate_answer(
        self,
        question_text: str,
        question_type: str,
        profile_facts: Dict[str, Any],
        job_context: Dict[str, Any],
        max_characters: Optional[int] = None
    ) -> Dict[str, Any]:
        pass


class LocalMockScreeningAIProvider(ScreeningAIProvider):
    """
    Local Mock Screening AI Provider producing grounded answers using candidate profile facts
    without requiring paid external commercial LLM API credentials.
    """

    def generate_answer(
        self,
        question_text: str,
        question_type: str,
        profile_facts: Dict[str, Any],
        job_context: Dict[str, Any],
        max_characters: Optional[int] = None
    ) -> Dict[str, Any]:
        candidate_name = profile_facts.get("full_name", "the candidate")
        role = profile_facts.get("current_role", "Software Professional")
        years = profile_facts.get("years_of_experience", 0)
        skills = profile_facts.get("skills", [])
        job_title = job_context.get("title", "this role")
        company = job_context.get("company_name", "Acme")

        # 1. Motivation / Role Interest
        if question_type == "ROLE_INTEREST":
            ans = f"I am excited to apply for the {job_title} position at {company}. With {years} years of experience as a {role} and technical skills in {', '.join(skills[:3]) if skills else 'software engineering'}, I am eager to contribute to your team's success."
            return {"status": "SUCCESS", "answer": ans, "confidence": 0.90}

        # 2. Company Interest
        if question_type == "COMPANY_INTEREST":
            ans = f"I admire {company}'s work and commitment to quality engineering. As a {role} experienced in {', '.join(skills[:2]) if skills else 'software design'}, I look forward to bringing my skills to your projects."
            return {"status": "SUCCESS", "answer": ans, "confidence": 0.88}

        # 3. General Knowledge (e.g. "What is regression testing?")
        if "regression testing" in question_text.lower():
            ans = "Regression testing is a software testing practice that verifies that recently developed or updated code has not adversely affected existing functional features."
            return {"status": "SUCCESS", "answer": ans, "confidence": 0.95}

        # Fallback
        ans = f"As a {role} with {years} years of relevant experience, I bring solid skills in {', '.join(skills[:3]) if skills else 'problem solving'} to the {job_title} position."
        return {"status": "SUCCESS", "answer": ans, "confidence": 0.85}

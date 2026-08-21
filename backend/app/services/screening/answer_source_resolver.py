from typing import Dict, Any
from app.services.screening.taxonomy import QuestionType


class AnswerSourceResolver:
    """
    Answer Source Resolver determining where an answer should be sourced from:
    PROFILE, RESUME, JOB_DESCRIPTION, COMPANY_CONTEXT, DETERMINISTIC_RULE, AI_GENERATED, HUMAN, GENERAL_KNOWLEDGE
    """

    @staticmethod
    def resolve_source(question_type: str, question_text: str) -> str:
        # 1. Pure Deterministic Profile Facts
        if question_type in [
            QuestionType.LOCATION,
            QuestionType.RELOCATION,
            QuestionType.WORK_AUTHORIZATION,
            QuestionType.SPONSORSHIP,
            QuestionType.SALARY,
            QuestionType.EDUCATION,
            QuestionType.CONTACT_INFORMATION
        ]:
            return "DETERMINISTIC_RULE"

        # 2. General Knowledge Technical Questions
        text_lower = question_text.lower()
        if "what is" in text_lower or "explain what" in text_lower or "define" in text_lower:
            return "GENERAL_KNOWLEDGE"

        # 3. Role / Motivation Interest -> Profile + Job Description AI Generation
        if question_type in [QuestionType.ROLE_INTEREST, QuestionType.MOTIVATION]:
            return "PROFILE_PLUS_JOB_DESCRIPTION"

        # 4. Company Interest -> Profile + Company Context
        if question_type == QuestionType.COMPANY_INTEREST:
            return "PROFILE_PLUS_COMPANY_CONTEXT"

        # 5. Experience / Project / Skill -> Profile + Resume
        if question_type in [QuestionType.EXPERIENCE, QuestionType.PROJECT, QuestionType.SKILL, QuestionType.TECHNICAL]:
            return "PROFILE_PLUS_RESUME"

        return "AI_GENERATED"

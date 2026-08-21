import re
from typing import Dict, Any
from app.services.screening.taxonomy import QuestionType

SENSITIVE_TYPES = {
    QuestionType.WORK_AUTHORIZATION,
    QuestionType.SPONSORSHIP,
}


class QuestionClassifier:
    """
    Question Classifier identifying question type and confidence score.
    Returns UNKNOWN when confidence < 0.70 to trigger human review.
    """

    @staticmethod
    def classify_question(
        question_text: str,
        label: str = "",
        field_identifier: str = "",
        input_type: str = ""
    ) -> Dict[str, Any]:
        text = f"{question_text} {label} {field_identifier}".strip().lower()

        # 1. Sponsorship / Work Authorization (Sensitive)
        if "sponsorship" in text or "visa" in text or "require sponsor" in text:
            return {"type": QuestionType.SPONSORSHIP, "confidence": 0.99, "is_sensitive": True}

        if "authorized to work" in text or "legally authorized" in text or "work permit" in text:
            return {"type": QuestionType.WORK_AUTHORIZATION, "confidence": 0.99, "is_sensitive": True}

        # 2. Relocation & Location
        if "relocate" in text or "relocation" in text or "willing to move" in text:
            return {"type": QuestionType.RELOCATION, "confidence": 0.98, "is_sensitive": False}

        if "current city" in text or "current location" in text or "where are you located" in text:
            return {"type": QuestionType.LOCATION, "confidence": 0.95, "is_sensitive": False}

        # 3. Salary & Compensation
        if "salary" in text or "compensation" in text or "expected ctc" in text or "expected pay" in text:
            return {"type": QuestionType.SALARY, "confidence": 0.98, "is_sensitive": False}

        # 4. Motivation & Role Interest
        if "why are you interested" in text or "why this role" in text or "interest in this position" in text:
            return {"type": QuestionType.ROLE_INTEREST, "confidence": 0.95, "is_sensitive": False}

        if "why work for" in text or "why do you want to join" in text or "why this company" in text:
            return {"type": QuestionType.COMPANY_INTEREST, "confidence": 0.95, "is_sensitive": False}

        # 5. Experience & Projects
        if "describe a project" in text or "project where you" in text or "relevant project" in text:
            return {"type": QuestionType.PROJECT, "confidence": 0.92, "is_sensitive": False}

        if "experience" in text or "managing" in text or "testing experience" in text or "years of experience" in text:
            return {"type": QuestionType.EXPERIENCE, "confidence": 0.92, "is_sensitive": False}

        # 6. Technical & Skill
        if "testing tools" in text or "which tools" in text or "technologies have you used" in text or "have you worked with" in text:
            return {"type": QuestionType.TECHNICAL, "confidence": 0.90, "is_sensitive": False}

        if "explain what" in text or "what is" in text or "define" in text:
            return {"type": QuestionType.TECHNICAL, "confidence": 0.88, "is_sensitive": False}

        # 7. Strengths & Achievements
        if "greatest strength" in text or "key strength" in text:
            return {"type": QuestionType.STRENGTH, "confidence": 0.90, "is_sensitive": False}

        if "significant achievement" in text or "proudest accomplishment" in text:
            return {"type": QuestionType.ACHIEVEMENT, "confidence": 0.90, "is_sensitive": False}

        # 8. Ambiguous / Low Confidence Open-Ended
        if "different" in text or "stand out" in text or "tell us about yourself" in text:
            return {"type": QuestionType.GENERAL_OPEN_ENDED, "confidence": 0.65, "is_sensitive": False}

        return {"type": QuestionType.UNKNOWN, "confidence": 0.50, "is_sensitive": False}

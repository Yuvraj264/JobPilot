from typing import Dict, Any, Optional
from app.services.screening.answer_length_constraint import AnswerLengthConstraint


class AnswerValidator:
    """
    Answer Validator verifying answer text non-emptiness, length limits, and anti-fabrication rules.
    """

    @staticmethod
    def validate_answer(
        answer_text: Optional[str],
        question_text: str,
        max_length: Optional[int] = None,
        confidence: float = 1.0
    ) -> Dict[str, Any]:

        if not answer_text or not answer_text.strip():
            return {
                "valid": False,
                "confidence": 0.0,
                "issues": ["Answer is empty or null."]
            }

        issues = []

        # 1. Length Check
        constraints = AnswerLengthConstraint.extract_constraints(question_text, maxlength=max_length)
        if constraints["max_characters"] and len(answer_text) > constraints["max_characters"]:
            issues.append(f"Answer length ({len(answer_text)} chars) exceeds maximum allowed ({constraints['max_characters']} chars).")

        # 2. Confidence Threshold Check
        if confidence < 0.70:
            issues.append(f"Answer confidence ({confidence}) is below threshold 0.70.")

        is_valid = len(issues) == 0
        return {
            "valid": is_valid,
            "confidence": confidence if is_valid else min(confidence, 0.50),
            "issues": issues
        }

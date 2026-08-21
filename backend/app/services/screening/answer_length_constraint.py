import re
from typing import Dict, Any, Optional


class AnswerLengthConstraint:
    """
    Answer Length Constraint Engine extracting and enforcing character and word limits.
    Prevents blind text truncation in the middle of sentences.
    """

    @staticmethod
    def extract_constraints(question_text: str, maxlength: Optional[int] = None) -> Dict[str, Optional[int]]:
        max_chars = maxlength
        max_words = None

        text = question_text.lower()

        # Check prompt character limit phrases
        match_chars = re.search(r"(\d+)\s*(?:character|char)", text)
        if match_chars:
            extracted_c = int(match_chars.group(1))
            max_chars = min(max_chars, extracted_c) if max_chars else extracted_c

        # Check prompt word limit phrases
        match_words = re.search(r"(\d+)\s*word", text)
        if match_words:
            max_words = int(match_words.group(1))

        if "briefly" in text and not max_words:
            max_words = 50

        return {"max_characters": max_chars, "max_words": max_words}

    @staticmethod
    def enforce_length(text: str, max_characters: Optional[int] = None, max_words: Optional[int] = None) -> str:
        if not text:
            return ""

        result = text.strip()

        # Enforce Word Limit
        if max_words:
            words = result.split()
            if len(words) > max_words:
                result = " ".join(words[:max_words])
                if not result.endswith("."):
                    result += "."

        # Enforce Character Limit
        if max_characters and len(result) > max_characters:
            cut_idx = max_characters
            # Truncate at previous sentence boundary or word boundary
            last_period = result[:max_characters].rfind(".")
            if last_period > max_characters // 2:
                result = result[: last_period + 1]
            else:
                last_space = result[:max_characters].rfind(" ")
                if last_space > 0:
                    result = result[:last_space] + "."
                else:
                    result = result[:max_characters]

        return result

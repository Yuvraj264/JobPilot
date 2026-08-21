from typing import Optional

EMPLOYMENT_TYPE_MAP = {
    "full-time": "FULL_TIME",
    "fulltime": "FULL_TIME",
    "full_time": "FULL_TIME",
    "permanent": "FULL_TIME",
    "direct hire": "FULL_TIME",
    "part-time": "PART_TIME",
    "parttime": "PART_TIME",
    "part_time": "PART_TIME",
    "contract": "CONTRACT",
    "contractor": "CONTRACT",
    "freelance": "CONTRACT",
    "internship": "INTERNSHIP",
    "intern": "INTERNSHIP",
    "temporary": "TEMPORARY",
    "temp": "TEMPORARY",
}


class EmploymentTypeNormalizer:
    """
    Employment Type Normalizer.
    Maps raw strings into controlled vocabulary: FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP, TEMPORARY, OTHER, UNKNOWN.
    """

    @staticmethod
    def normalize(raw_type: Optional[str]) -> str:
        if not raw_type or not raw_type.strip():
            return "UNKNOWN"

        key = raw_type.strip().lower()
        if key in EMPLOYMENT_TYPE_MAP:
            return EMPLOYMENT_TYPE_MAP[key]

        for pattern, normalized in EMPLOYMENT_TYPE_MAP.items():
            if pattern in key:
                return normalized

        return "UNKNOWN"

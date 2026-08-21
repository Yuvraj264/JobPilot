from typing import Optional

WORKPLACE_TYPE_MAP = {
    "remote": "REMOTE",
    "work from home": "REMOTE",
    "wfh": "REMOTE",
    "telecommute": "REMOTE",
    "virtual": "REMOTE",
    "hybrid": "HYBRID",
    "flexible": "HYBRID",
    "onsite": "ONSITE",
    "on-site": "ONSITE",
    "in-office": "ONSITE",
    "office": "ONSITE",
}


class WorkplaceTypeNormalizer:
    """
    Workplace Type Normalizer.
    Maps raw strings into ONSITE, HYBRID, REMOTE, UNKNOWN.
    """

    @staticmethod
    def normalize(raw_type: Optional[str]) -> str:
        if not raw_type or not raw_type.strip():
            return "UNKNOWN"

        key = raw_type.strip().lower()
        if key in WORKPLACE_TYPE_MAP:
            return WORKPLACE_TYPE_MAP[key]

        for pattern, normalized in WORKPLACE_TYPE_MAP.items():
            if pattern in key:
                return normalized

        return "UNKNOWN"

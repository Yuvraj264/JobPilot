import re
from typing import Optional, Tuple

KNOWN_LOCATION_MAP = {
    "bangalore": "Bengaluru, India",
    "bengaluru": "Bengaluru, India",
    "bangalore, india": "Bengaluru, India",
    "bengaluru, india": "Bengaluru, India",
    "mumbai": "Mumbai, India",
    "delhi": "Delhi, India",
    "remote": "Remote",
    "remote - india": "Remote, India",
    "remote, india": "Remote, India",
    "san francisco": "San Francisco, CA, USA",
    "san francisco, ca": "San Francisco, CA, USA",
    "new york": "New York, NY, USA",
    "new york, ny": "New York, NY, USA",
    "seattle": "Seattle, WA, USA",
    "seattle, wa": "Seattle, WA, USA",
    "austin": "Austin, TX, USA",
    "austin, tx": "Austin, TX, USA",
    "chicago": "Chicago, IL, USA",
    "chicago, il": "Chicago, IL, USA",
    "boston": "Boston, MA, USA",
    "boston, ma": "Boston, MA, USA",
}


class LocationNormalizer:
    """
    Location Normalization Service.
    Standardizes city/country variants without altering ambiguous text when uncertain.
    """

    @staticmethod
    def normalize(raw_location: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Returns: (cleaned_location, standardized_location)
        """
        if not raw_location or not raw_location.strip():
            return None, None

        cleaned = re.sub(r"\s+", " ", raw_location.strip())
        key = cleaned.lower()

        if key in KNOWN_LOCATION_MAP:
            return cleaned, KNOWN_LOCATION_MAP[key]

        # General cleaning heuristics
        if "remote" in key:
            if "india" in key:
                return cleaned, "Remote, India"
            elif "us" in key or "usa" in key:
                return cleaned, "Remote, USA"
            return cleaned, "Remote"

        return cleaned, cleaned

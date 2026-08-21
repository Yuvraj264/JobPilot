from typing import Dict, List, Any, Optional
from app.services.adapters.base import (
    JobSourceAdapter,
    UnsupportedOperationError,
)


class LinkedInJobSourceAdapter(JobSourceAdapter):
    """
    Adapter for LinkedIn Job Source.
    Does NOT execute web scraping or private API reverse engineering to respect platform policies.
    """

    def source_name(self) -> str:
        return "linkedin"

    def display_name(self) -> str:
        return "LinkedIn Job Platform"

    def source_type(self) -> str:
        return "BROWSER"

    def discover_jobs(self, limit: int = 50, page: int = 1) -> List[Dict[str, Any]]:
        raise UnsupportedOperationError(
            "LinkedIn automated job discovery is not supported without partner API access. Use HUMAN_ASSISTED mode."
        )

    def get_job_details(self, external_id: str) -> Optional[Dict[str, Any]]:
        raise UnsupportedOperationError(
            "LinkedIn automated job detail retrieval is not supported. Use HUMAN_ASSISTED mode."
        )

    def health_check(self) -> str:
        return "unsupported"

    def metadata(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name(),
            "display_name": self.display_name(),
            "source_type": self.source_type(),
            "supported_access_method": "Human Assisted Browser Session",
            "requires_authentication": True,
            "requires_human_interaction": True,
            "automation_allowed": False,
            "capabilities": {
                "DISCOVERY": False,
                "APPLICATION": False,
                "BROWSER": True,
                "API": False,
                "FEED": False,
                "HUMAN_ASSISTED": True,
            },
            "status": "UNAVAILABLE",
            "notes": "Automated scraping is prohibited by LinkedIn terms. Only human-assisted manual session is permitted.",
        }

from typing import Dict, List, Any, Optional
from app.services.adapters.base import (
    JobSourceAdapter,
    UnsupportedOperationError,
)


class IndeedJobSourceAdapter(JobSourceAdapter):
    """
    Adapter for Indeed Job Platform.
    Does NOT execute web scraping to respect platform guidelines.
    """

    def source_name(self) -> str:
        return "indeed"

    def display_name(self) -> str:
        return "Indeed Job Platform"

    def source_type(self) -> str:
        return "WEB"

    def discover_jobs(self, limit: int = 50, page: int = 1) -> List[Dict[str, Any]]:
        raise UnsupportedOperationError(
            "Indeed automated job discovery is deprecated and unsupported. Use CompanyCareersAdapter."
        )

    def get_job_details(self, external_id: str) -> Optional[Dict[str, Any]]:
        raise UnsupportedOperationError(
            "Indeed automated job detail retrieval is unsupported. Use CompanyCareersAdapter."
        )

    def health_check(self) -> str:
        return "unsupported"

    def metadata(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name(),
            "display_name": self.display_name(),
            "source_type": self.source_type(),
            "supported_access_method": "None (Publisher API deprecated)",
            "requires_authentication": False,
            "requires_human_interaction": False,
            "automation_allowed": False,
            "capabilities": {
                "DISCOVERY": False,
                "APPLICATION": False,
                "BROWSER": False,
                "API": False,
                "FEED": False,
                "HUMAN_ASSISTED": False,
            },
            "status": "UNAVAILABLE",
            "notes": "Publisher API is retired. Direct scraping violates Indeed terms of service.",
        }

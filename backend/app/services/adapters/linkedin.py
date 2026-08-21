from typing import Dict, List, Any, Optional
from app.services.adapters.base import JobSourceAdapter


class LinkedInJobSourceAdapter(JobSourceAdapter):
    """
    Placeholder Adapter for LinkedIn Job Source.
    Does NOT execute web scraping or browser automation in Phase 4.
    """

    def source_name(self) -> str:
        return "linkedin"

    def display_name(self) -> str:
        return "LinkedIn Job Platform"

    def source_type(self) -> str:
        return "BROWSER"

    def discover_jobs(self, limit: int = 50, page: int = 1) -> List[Dict[str, Any]]:
        raise NotImplementedError("LinkedIn job discovery is not implemented in Phase 4. Use MockJobSourceAdapter.")

    def get_job_details(self, external_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("LinkedIn job details retrieval is not implemented in Phase 4.")

    def health_check(self) -> bool:
        return False

    def metadata(self) -> Dict[str, Any]:
        meta = super().metadata()
        meta["supported_access_method"] = "Permitted API / Browser Automation (Placeholder)"
        meta["requires_authentication"] = True
        meta["requires_human_interaction"] = True
        meta["automation_allowed"] = False
        meta["notes"] = "Placeholder adapter. Real integration requires explicit permission and authentication in future phases."
        return meta

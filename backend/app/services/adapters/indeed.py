from typing import Dict, List, Any, Optional
from app.services.adapters.base import JobSourceAdapter


class IndeedJobSourceAdapter(JobSourceAdapter):
    """
    Placeholder Adapter for Indeed Job Platform.
    Does NOT execute web scraping or browser automation in Phase 4.
    """

    def source_name(self) -> str:
        return "indeed"

    def display_name(self) -> str:
        return "Indeed Job Platform"

    def source_type(self) -> str:
        return "WEB"

    def discover_jobs(self, limit: int = 50, page: int = 1) -> List[Dict[str, Any]]:
        raise NotImplementedError("Indeed job discovery is not implemented in Phase 4. Use MockJobSourceAdapter.")

    def get_job_details(self, external_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Indeed job details retrieval is not implemented in Phase 4.")

    def health_check(self) -> bool:
        return False

    def metadata(self) -> Dict[str, Any]:
        meta = super().metadata()
        meta["supported_access_method"] = "Permitted RSS Feed / Public API (Placeholder)"
        meta["notes"] = "Placeholder adapter. Real integration requires explicit permission and API access in future phases."
        return meta

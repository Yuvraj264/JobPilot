from typing import Dict, List, Any, Optional
from app.services.adapters.base import JobSourceAdapter


class CompanyCareersJobSourceAdapter(JobSourceAdapter):
    """
    Placeholder Adapter for Direct Company Career Pages.
    Does NOT execute web scraping in Phase 4.
    """

    def source_name(self) -> str:
        return "company_careers"

    def display_name(self) -> str:
        return "Company Career Pages"

    def source_type(self) -> str:
        return "WEB"

    def discover_jobs(self, limit: int = 50, page: int = 1) -> List[Dict[str, Any]]:
        raise NotImplementedError("Company Career page discovery is not implemented in Phase 4. Use MockJobSourceAdapter.")

    def get_job_details(self, external_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Company Career job details retrieval is not implemented in Phase 4.")

    def health_check(self) -> bool:
        return False

    def metadata(self) -> Dict[str, Any]:
        meta = super().metadata()
        meta["supported_access_method"] = "Public ATS API / Feed (Placeholder)"
        meta["notes"] = "Placeholder adapter for direct company career portals."
        return meta

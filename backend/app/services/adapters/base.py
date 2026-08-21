from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class JobSourceAdapter(ABC):
    """
    Abstract Base Class for all Job Source Adapters (Mock, LinkedIn, Indeed, Company Careers, etc.).
    Defines unified discovery interface, type hints, and platform compliance metadata.
    """

    @abstractmethod
    def source_name(self) -> str:
        """Unique machine identifier for source (e.g., 'mock', 'linkedin')."""
        pass

    @abstractmethod
    def display_name(self) -> str:
        """Human readable display name (e.g., 'Mock Job Source')."""
        pass

    @abstractmethod
    def source_type(self) -> str:
        """Source type: API, RSS, WEB, BROWSER, MANUAL."""
        pass

    @abstractmethod
    def discover_jobs(self, limit: int = 50, page: int = 1) -> List[Dict[str, Any]]:
        """
        Discovers raw job postings from source.
        Returns a list of raw job dictionaries.
        """
        pass

    @abstractmethod
    def get_job_details(self, external_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves raw job details for a specific external job ID."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Performs a health check verifying source connectivity or status."""
        pass

    def metadata(self) -> Dict[str, Any]:
        """
        Returns compliance and capability metadata for this source.
        """
        return {
            "source_name": self.source_name(),
            "display_name": self.display_name(),
            "source_type": self.source_type(),
            "supported_access_method": "JSON Fixture / Permitted Feed",
            "requires_authentication": False,
            "requires_human_interaction": False,
            "automation_allowed": True,
            "notes": "Standard adapter implementation adhering to platform compliance boundaries.",
        }

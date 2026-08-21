from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ApplicationTarget(ABC):
    """
    Abstract Generic Application Target.
    Insulates the application agent from platform-specific site structures.
    """

    @abstractmethod
    def target_name(self) -> str:
        pass

    @abstractmethod
    def get_start_url(self, job_id: int) -> str:
        pass

    @abstractmethod
    def verify_page_state(self, current_url: str, page_title: str) -> bool:
        pass

    def requires_human_authentication(self) -> bool:
        return False


class MockApplicationTarget(ApplicationTarget):
    """
    Concrete Local Mock Application Target.
    """

    def target_name(self) -> str:
        return "mock"

    def get_start_url(self, job_id: int) -> str:
        from app.api.mock_app_routes import ensure_mock_html_files
        return ensure_mock_html_files()

    def verify_page_state(self, current_url: str, page_title: str) -> bool:
        return "step" in current_url or "review" in current_url or "mock" in current_url


class LinkedInApplicationTarget(ApplicationTarget):
    """
    Placeholder LinkedIn Target (Raises NotImplementedError to strictly prevent external platform scraping).
    """

    def target_name(self) -> str:
        return "linkedin"

    def get_start_url(self, job_id: int) -> str:
        raise NotImplementedError("LinkedIn application automation is NOT implemented in Phase 6.")

    def verify_page_state(self, current_url: str, page_title: str) -> bool:
        raise NotImplementedError("LinkedIn application automation is NOT implemented in Phase 6.")


class IndeedApplicationTarget(ApplicationTarget):
    """
    Placeholder Indeed Target (Raises NotImplementedError).
    """

    def target_name(self) -> str:
        return "indeed"

    def get_start_url(self, job_id: int) -> str:
        raise NotImplementedError("Indeed application automation is NOT implemented in Phase 6.")


class CompanyCareerApplicationTarget(ApplicationTarget):
    """
    Placeholder Company Career Site Target (Raises NotImplementedError).
    """

    def target_name(self) -> str:
        return "company_careers"

    def get_start_url(self, job_id: int) -> str:
        raise NotImplementedError("Company Career site automation is NOT implemented in Phase 6.")

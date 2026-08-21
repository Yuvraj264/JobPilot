from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.services.automation.browser_session import ApplicationBrowserSession


class ApplicationAdapter(ABC):
    """
    Abstract Base Class representing a Job Application Target Adapter.
    """
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def display_name(self) -> str:
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Returns capability model, e.g.:
        {
            "form_filling": bool,
            "resume_upload": bool,
            "question_processing": bool,
            "submission": bool,
            "human_assisted": bool,
            "authentication": bool,
            "captcha_required": bool
        }
        """
        pass

    @abstractmethod
    def open_application(self, session: ApplicationBrowserSession, url: str) -> str:
        pass

    @abstractmethod
    def inspect(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        pass

    @abstractmethod
    def prepare_application(self, session: ApplicationBrowserSession, package: Any) -> Dict[str, Any]:
        pass

    @abstractmethod
    def execute_actions(
        self,
        session: ApplicationBrowserSession,
        actions: List[Dict[str, Any]],
        db: Any,
        run_id: int
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def detect_intervention(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        pass

    @abstractmethod
    def submit(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        pass

    @abstractmethod
    def verify_submission(self, session: ApplicationBrowserSession, submit_result: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def close(self, session: ApplicationBrowserSession):
        pass

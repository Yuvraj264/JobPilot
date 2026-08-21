from typing import Dict, Any, List
from app.services.automation.adapters.base import ApplicationAdapter
from app.services.automation.browser_session import ApplicationBrowserSession


class IndeedApplicationAdapter(ApplicationAdapter):
    """
    Indeed adapter implementing human-assisted execution to strictly comply with platform policies.
    """
    def name(self) -> str:
        return "indeed"

    def display_name(self) -> str:
        return "Indeed Apply"

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            "form_filling": False,
            "resume_upload": False,
            "question_processing": False,
            "submission": False,
            "human_assisted": True,
            "authentication": True,
            "captcha_required": True
        }

    def open_application(self, session: ApplicationBrowserSession, url: str) -> str:
        return session.navigate(url)

    def inspect(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        return {"has_captcha": False, "login_required": True, "fields": []}

    def prepare_application(self, session: ApplicationBrowserSession, package: Any) -> Dict[str, Any]:
        return {}

    def execute_actions(
        self,
        session: ApplicationBrowserSession,
        actions: List[Dict[str, Any]],
        db: Any,
        run_id: int
    ) -> List[Dict[str, Any]]:
        return []

    def detect_intervention(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        # Always request user intervention on Indeed Easy Apply
        return {
            "required": True,
            "type": "LOGIN_REQUIRED",
            "reason": "Indeed Easy Apply automation is restricted. Please sign in and complete Easy Apply manually in the browser window."
        }

    def submit(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        return {"success": False, "error": "Automated submission is unsupported on Indeed. Please submit manually."}

    def verify_submission(self, session: ApplicationBrowserSession, submit_result: Dict[str, Any]) -> bool:
        page = session.page
        if not page:
            return False
        content = page.content().lower()
        if "application submitted" in content or "your application has been sent" in content:
            return True
        return False

    def close(self, session: ApplicationBrowserSession):
        session.stop()

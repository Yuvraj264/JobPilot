from typing import Dict, Any, List
from app.services.automation.adapters.base import ApplicationAdapter
from app.services.automation.browser_session import ApplicationBrowserSession


class LinkedInApplicationAdapter(ApplicationAdapter):
    """
    LinkedIn adapter implementing human-assisted and manual application actions to strictly prevent automated anti-bot violations.
    """
    def name(self) -> str:
        return "linkedin"

    def display_name(self) -> str:
        return "LinkedIn Easy Apply"

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
        # Always request user intervention on LinkedIn Easy Apply to allow user control
        return {
            "required": True,
            "type": "LOGIN_REQUIRED",
            "reason": "LinkedIn automation is restricted. Please log in and complete Easy Apply manually in the browser window."
        }

    def submit(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        return {"success": False, "error": "Automated Easy Apply submission is unsupported on LinkedIn. Please click submit manually."}

    def verify_submission(self, session: ApplicationBrowserSession, submit_result: Dict[str, Any]) -> bool:
        page = session.page
        if not page:
            return False
        # If user submits manually, check if success confirmation is displayed
        content = page.content().lower()
        if "application sent" in content or "submitted" in content or "success" in page.url.lower():
            return True
        return False

    def close(self, session: ApplicationBrowserSession):
        session.stop()

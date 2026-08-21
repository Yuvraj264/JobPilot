from typing import Dict, Any, List
import logging
from app.services.automation.adapters.base import ApplicationAdapter
from app.services.automation.browser_session import ApplicationBrowserSession
from app.services.automation.page_inspector import PageInspector
from app.services.automation.action_planner import ApplicationActionPlanner
from app.services.automation.action_executor import ApplicationActionExecutor

logger = logging.getLogger(__name__)


class GenericCareerApplicationAdapter(ApplicationAdapter):
    """
    Adapter implementing page form filing and human-assisted automation for generic career sites.
    """
    def name(self) -> str:
        return "generic_career"

    def display_name(self) -> str:
        return "Company Careers Portal"

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            "form_filling": True,
            "resume_upload": True,
            "question_processing": True,
            "submission": False,  # Default to false for safety
            "human_assisted": True,
            "authentication": False,
            "captcha_required": False
        }

    def open_application(self, session: ApplicationBrowserSession, url: str) -> str:
        return session.navigate(url)

    def inspect(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        if not session.page:
            return {"has_captcha": False, "login_required": False, "fields": []}
        return PageInspector.inspect_page(session.page)

    def prepare_application(self, session: ApplicationBrowserSession, package: Any) -> Dict[str, Any]:
        return self.inspect(session)

    def execute_actions(
        self,
        session: ApplicationBrowserSession,
        actions: List[Dict[str, Any]],
        db: Any,
        run_id: int
    ) -> List[Dict[str, Any]]:
        results = []
        for act in actions:
            if act.get("action") == "PAUSE_FOR_HUMAN":
                results.append({"status": "PAUSED", "reason": act.get("reason", "Human intervention requested.")})
                break
            res = ApplicationActionExecutor.execute_action(db, run_id, session.controller, act)
            results.append(res)
        return results

    def detect_intervention(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        inspection = self.inspect(session)
        if inspection.get("has_captcha"):
            return {"required": True, "type": "CAPTCHA_DETECTED", "reason": "CAPTCHA widget detected."}
        if "login" in session.current_url().lower():
            return {"required": True, "type": "LOGIN_REQUIRED", "reason": "Login required."}
        return {"required": False}

    def submit(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        # Submissions on real career pages defaults to manual/human-assisted
        return {"success": False, "error": "Generic Company Careers submission is restricted. Please review and click submit manually."}

    def verify_submission(self, session: ApplicationBrowserSession, submit_result: Dict[str, Any]) -> bool:
        page = session.page
        if not page:
            return False
        # Fallback success check
        content = page.content().lower()
        if "thank you" in content or "received" in content or "success" in page.url.lower():
            return True
        return False

    def close(self, session: ApplicationBrowserSession):
        session.stop()

from typing import Dict, Any, List
from urllib.parse import urljoin
import logging
from app.services.automation.adapters.base import ApplicationAdapter
from app.services.automation.browser_session import ApplicationBrowserSession
from app.services.automation.page_inspector import PageInspector
from app.services.automation.action_planner import ApplicationActionPlanner
from app.services.automation.action_executor import ApplicationActionExecutor

logger = logging.getLogger(__name__)


class MockApplicationAdapter(ApplicationAdapter):
    """
    Adapter implementing full automation for the local mock application server.
    """
    def name(self) -> str:
        return "mock"

    def display_name(self) -> str:
        return "Local Mock App Portal"

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            "form_filling": True,
            "resume_upload": True,
            "question_processing": True,
            "submission": True,
            "human_assisted": False,
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
        # Returns action plan based on current page state and application package content
        inspection = self.inspect(session)
        # Note: package fields will be resolved by PageInspector/ActionPlanner
        return inspection

    def execute_actions(
        self,
        session: ApplicationBrowserSession,
        actions: List[Dict[str, Any]],
        db: Any,
        run_id: int
    ) -> List[Dict[str, Any]]:
        results = []
        for act in actions:
            res = ApplicationActionExecutor.execute_action(db, run_id, session.controller, act)
            results.append(res)
        return results

    def detect_intervention(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        inspection = self.inspect(session)
        # Mock captcha / intervention detection
        if inspection.get("has_captcha"):
            return {"required": True, "type": "CAPTCHA_DETECTED", "reason": "CAPTCHA challenge detected."}
        if "login" in session.current_url().lower():
            return {"required": True, "type": "LOGIN_REQUIRED", "reason": "Login requested."}
        return {"required": False}

    def submit(self, session: ApplicationBrowserSession) -> Dict[str, Any]:
        page = session.page
        if not page:
            return {"success": False, "error": "No active page."}

        # Check if we are on the review page
        if "review" in page.url.lower():
            try:
                # Click the submit button
                submit_btn = page.locator("button#submit-btn, button[type='submit']").first
                if submit_btn.count() > 0:
                    submit_btn.click()
                    page.wait_for_load_state("networkidle", timeout=5000)
                    return {"success": True, "final_url": page.url}
            except Exception as e:
                return {"success": False, "error": f"Submit click error: {e}"}

        return {"success": False, "error": "Not on a review/submit page."}

    def verify_submission(self, session: ApplicationBrowserSession, submit_result: Dict[str, Any]) -> bool:
        page = session.page
        if not page:
            return False
        # Verify success indicators
        url_lower = page.url.lower()
        if "success" in url_lower or "confirm" in url_lower:
            return True
        content = page.content().lower()
        if "submitted successfully" in content or "confirmation" in content:
            return True
        return False

    def close(self, session: ApplicationBrowserSession):
        session.stop()

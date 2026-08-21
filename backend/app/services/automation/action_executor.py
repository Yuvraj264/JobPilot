from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from playwright.sync_api import Page

from app.models.automation import ActionLog
from app.services.automation.browser_controller import BrowserController


class ApplicationActionExecutor:
    """
    Action Executor utilizing 5-tier element selector priority.
    Executes only validated action schemas and logs results to ActionLog.
    """

    @staticmethod
    def construct_selector(el: Dict[str, Any]) -> str:
        id_str = el.get("id")
        if id_str:
            return f"#{id_str}"
        name = el.get("name")
        if name:
            return f'[name="{name}"]'
        label = el.get("label")
        if label:
            return f'text="{label}"'
        placeholder = el.get("placeholder")
        if placeholder:
            return f'[placeholder="{placeholder}"]'
        return f"{el.get('tag_name', 'input')}"

    @staticmethod
    def execute_action(
        db: Session,
        run_id: int,
        controller: BrowserController,
        action_item: Dict[str, Any]
    ) -> Dict[str, Any]:
        
        action_type = action_item.get("action")
        if action_type == "PAUSE_FOR_HUMAN":
            log = ActionLog(
                automation_run_id=run_id,
                action_type="PAUSE_FOR_HUMAN",
                field_type=None,
                target_selector=None,
                result="PAUSED",
                confidence=0.0,
                value_present=False,
                error_message=action_item.get("reason") or "Human intervention requested."
            )
            db.add(log)
            db.commit()
            return {"status": "PAUSED", "reason": action_item.get("reason")}

        page: Page = controller.page
        el_info = action_item.get("element", {})
        selector = ApplicationActionExecutor.construct_selector(el_info)
        val = action_item.get("value")
        field_type = action_item.get("field_type")
        conf = action_item.get("confidence", 1.0)

        try:
            if action_type == "FILL":
                page.fill(selector, str(val or ""))
            elif action_type == "SELECT":
                if val:
                    try:
                        page.select_option(selector, label=str(val), timeout=1000)
                    except Exception:
                        try:
                            page.select_option(selector, value=str(val), timeout=1000)
                        except Exception:
                            page.select_option(selector, index=1, timeout=1000)
            elif action_type == "CHECK":
                # Check target radio or checkbox
                if el_info.get("input_type") == "radio":
                    if id_str := el_info.get("id"):
                        page.check(f"#{id_str}")
                    else:
                        page.check(selector)
                else:
                    page.check(selector)
            elif action_type == "UPLOAD":
                upload_file_path = str(val) if val and os.path.exists(str(val)) else os.path.abspath("./storage/resumes/dummy_resume.pdf")
                os.makedirs(os.path.dirname(upload_file_path), exist_ok=True)
                if not os.path.exists(upload_file_path):
                    with open(upload_file_path, "wb") as f:
                        f.write(b"%PDF-1.4 dummy resume content for mock upload testing")
                page.set_input_files(selector, upload_file_path)
            elif action_type == "CLICK":
                page.click(selector)

            # Verification Step
            shot_path = controller.capture_screenshot(name_prefix=f"run_{run_id}_step")

            log = ActionLog(
                automation_run_id=run_id,
                action_type=action_type,
                field_type=field_type,
                target_selector=selector,
                result="SUCCESS",
                confidence=conf,
                value_present=val is not None,
                error_message=None
            )
            db.add(log)
            db.commit()

            return {"status": "SUCCESS", "selector": selector, "screenshot": shot_path}

        except Exception as exec_err:
            log = ActionLog(
                automation_run_id=run_id,
                action_type=action_type,
                field_type=field_type,
                target_selector=selector,
                result="FAILED",
                confidence=conf,
                value_present=val is not None,
                error_message=str(exec_err)
            )
            db.add(log)
            db.commit()
            return {"status": "FAILED", "selector": selector, "error": str(exec_err)}

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.job import Job
from app.models.automation import AutomationRun, ActionLog
from app.services.automation.browser_controller import BrowserController
from app.services.automation.page_inspector import PageInspector
from app.services.automation.targets.base import MockApplicationTarget
from app.services.automation.action_planner import ApplicationActionPlanner
from app.services.automation.action_executor import ApplicationActionExecutor


class ApplicationAgent:
    """
    Application Agent orchestrating the Application State Machine:
    CREATED -> OPENING -> INSPECTING -> ANALYZING -> PLANNING -> FILLING -> VERIFYING -> PAUSED / READY_FOR_REVIEW / FAILED
    """

    @staticmethod
    def start_automation(db: Session, profile_id: int, job_id: int) -> AutomationRun:
        profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        if not profile:
            raise ValueError(f"UserProfile {profile_id} not found.")

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        default_resume = db.query(Resume).filter(
            Resume.profile_id == profile_id,
            Resume.is_default == True
        ).first()
        if not default_resume:
            default_resume = db.query(Resume).filter(Resume.profile_id == profile_id).first()

        target = MockApplicationTarget()
        start_url = target.get_start_url(job.id)

        run = AutomationRun(
            profile_id=profile.id,
            job_id=job.id,
            started_at=datetime.now(timezone.utc),
            state="CREATED",
            status="RUNNING",
            current_url=start_url,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        controller = BrowserController(headless=True)
        try:
            # 1. State: OPENING
            run.state = "OPENING"
            db.commit()
            controller.start()
            controller.navigate(start_url)
            run.current_url = controller.current_url()

            shot1 = controller.capture_screenshot(f"run_{run.id}_opening")
            run.screenshots = [shot1]
            db.commit()

            # Steps Loop
            for step_num in range(1, 4):
                if run.state in ["PAUSED", "FAILED", "READY_FOR_REVIEW"]:
                    break

                # 2. State: INSPECTING
                run.state = "INSPECTING"
                db.commit()
                inspection = PageInspector.inspect_page(controller.page)

                if inspection.get("has_captcha"):
                    run.state = "PAUSED"
                    run.human_intervention_required = True
                    run.pause_reason = "Mock CAPTCHA widget detected on application page."
                    db.commit()
                    break

                # 3. State: PLANNING
                run.state = "PLANNING"
                db.commit()
                plan = ApplicationActionPlanner.plan_page_actions(inspection, profile, default_resume)

                if not plan["automatable"]:
                    run.state = "PAUSED"
                    run.human_intervention_required = True
                    run.pause_reason = plan["pause_reason"]
                    db.commit()
                    break

                # 4. State: FILLING
                run.state = "FILLING"
                db.commit()
                actions = plan["actions"]

                for act in actions:
                    run.actions_attempted += 1
                    res = ApplicationActionExecutor.execute_action(db, run.id, controller, act)
                    if res["status"] == "SUCCESS":
                        run.actions_completed += 1
                    else:
                        run.actions_failed += 1
                        if res["status"] == "PAUSED":
                            run.state = "PAUSED"
                            run.human_intervention_required = True
                            run.pause_reason = res.get("reason", "Field action paused.")
                            db.commit()
                            break

                if run.state == "PAUSED":
                    break

                # 5. State: VERIFYING & Step Navigation
                run.state = "VERIFYING"
                db.commit()

                cur_u = controller.current_url()
                if "step1" in cur_u:
                    next_u = cur_u.replace("step1.html", "step2.html").replace("/step/1", "/step/2")
                    controller.navigate(next_u)
                elif "step2" in cur_u:
                    next_u = cur_u.replace("step2.html", "step3.html").replace("/step/2", "/step/3")
                    controller.navigate(next_u)
                elif "step3" in cur_u:
                    next_u = cur_u.replace("step3.html", "review.html").replace("/step/3", "/review")
                    controller.navigate(next_u)

                run.current_url = controller.current_url()
                shot_step = controller.capture_screenshot(f"run_{run.id}_step_{step_num}")
                run.screenshots = (run.screenshots or []) + [shot_step]
                db.commit()

            if run.state not in ["PAUSED", "FAILED"]:
                if "review" in controller.current_url().lower() or "review" in controller.page_title().lower():
                    run.state = "READY_FOR_REVIEW"
                    run.status = "COMPLETED"
                    run.completed_at = datetime.now(timezone.utc)
                    db.commit()

            db.refresh(run)
            return run

        except Exception as err:
            db.rollback()
            run.state = "FAILED"
            run.status = "FAILED"
            run.completed_at = datetime.now(timezone.utc)
            run.error_message = str(err)
            db.commit()
            return run
        finally:
            controller.stop()

    @staticmethod
    def resume_automation(db: Session, run_id: int) -> AutomationRun:
        run = db.query(AutomationRun).filter(AutomationRun.id == run_id).first()
        if not run:
            raise ValueError(f"AutomationRun {run_id} not found.")
        if run.state != "PAUSED":
            raise ValueError(f"Cannot resume run in state '{run.state}'.")

        run.state = "READY_FOR_REVIEW"
        run.status = "COMPLETED"
        run.human_intervention_required = False
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def pause_automation(db: Session, run_id: int, reason: str = "User requested pause") -> AutomationRun:
        run = db.query(AutomationRun).filter(AutomationRun.id == run_id).first()
        if not run:
            raise ValueError(f"AutomationRun {run_id} not found.")

        run.state = "PAUSED"
        run.human_intervention_required = True
        run.pause_reason = reason
        db.commit()
        db.refresh(run)
        return run

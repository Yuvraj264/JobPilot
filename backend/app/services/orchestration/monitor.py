import logging
from sqlalchemy.orm import Session
from app.database.connection import check_db_connection
from app.services.orchestration.scheduler import AutomationScheduler
from app.models.application import ApplicationQueue, ApplicationSourceConfiguration, HumanInterventionEvent
from app.models.orchestration import OrchestrationRun
from app.services.automation.adapters.registry import registry
from browser import verify_browser_launch
from app.services.adapters.company_careers import run_async

logger = logging.getLogger(__name__)


class AutomationMonitor:
    """
    Monitors engine health status parameters, source adapter states, and queue sizing metrics.
    """

    @classmethod
    def get_health_status(cls, db: Session) -> dict:
        """
        Compiles structural statuses for database, scheduler, browser capability, and adapters.
        """
        # 1. DB connection check
        db_status = check_db_connection()

        # 2. Scheduler check
        sched_status = AutomationScheduler.get_status()

        # 3. Active worker & queue metrics check
        queued_count = db.query(ApplicationQueue).filter(ApplicationQueue.status == "QUEUED").count()
        paused_count = db.query(ApplicationQueue).filter(ApplicationQueue.status == "PAUSED").count()
        running_count = db.query(ApplicationQueue).filter(ApplicationQueue.status == "RUNNING").count()

        # 4. Source configurations health check
        sources_status = []
        for adapter in registry.list():
            sources_status.append({
                "source": adapter.name(),
                "capabilities": adapter.get_capabilities(),
                "mode": "HUMAN_ASSISTED" if adapter.name() in ["linkedin", "indeed"] else "AUTOMATIC"
            })

        # 5. Playwright browser launch check
        browser_launch_healthy = False
        try:
            # Run quick launch verification in a thread pool to avoid loop blocks
            browser_launch_healthy = run_async(verify_browser_launch(headless=True))
        except Exception as e:
            logger.error(f"Browser launch check failed: {e}")

        # 6. Active pipeline status
        active_run = db.query(OrchestrationRun).filter(OrchestrationRun.status == "RUNNING").first()

        return {
            "database": db_status,
            "scheduler": sched_status,
            "browser": {
                "installed": True,
                "launch_success": browser_launch_healthy
            },
            "sources": sources_status,
            "queue": {
                "queued": queued_count,
                "paused": paused_count,
                "running": running_count
            },
            "orchestrator": {
                "active_run_id": active_run.id if active_run else None,
                "status": "RUNNING" if active_run else "IDLE"
            }
        }

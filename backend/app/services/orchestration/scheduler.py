import threading
import time
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal

logger = logging.getLogger(__name__)


class AutomationScheduler:
    """
    Local lightweight scheduling loop coordinating scheduled pipeline triggers.
    Remains disabled by default. Runs on a background thread.
    """

    _thread: Optional[threading.Thread] = None
    _stop_event = threading.Event()
    
    # In-memory configuration variables
    enabled = False
    schedule_type = "daily"  # hourly, daily, selected_days
    selected_days: List[int] = []  # 0=Monday, 6=Sunday
    scheduled_hour = 9  # 9 AM default
    scheduled_minute = 0
    
    last_run_time: Optional[datetime] = None

    @classmethod
    def start(cls):
        """Starts the scheduler thread loop if enabled."""
        if not cls.enabled:
            logger.info("Scheduler is disabled in configuration. Startup ignored.")
            return

        if cls._thread and cls._thread.is_alive():
            logger.info("Scheduler thread is already running.")
            return

        cls._stop_event.clear()
        cls._thread = threading.Thread(target=cls._loop, daemon=True)
        cls._thread.start()
        logger.info("Automation scheduler background thread started.")

    @classmethod
    def stop(cls):
        """Stops the scheduler thread loop."""
        cls._stop_event.set()
        if cls._thread:
            cls._thread.join(timeout=2.0)
            cls._thread = None
        logger.info("Automation scheduler background thread stopped.")

    @classmethod
    def get_status(cls) -> dict:
        """Returns scheduler run status metrics."""
        return {
            "enabled": cls.enabled,
            "running": cls._thread is not None and cls._thread.is_alive(),
            "schedule_type": cls.schedule_type,
            "scheduled_hour": cls.scheduled_hour,
            "scheduled_minute": cls.scheduled_minute,
            "selected_days": cls.selected_days,
            "last_run_time": cls.last_run_time.isoformat() if cls.last_run_time else None
        }

    @classmethod
    def update_config(cls, data: dict):
        """Updates scheduling configuration parameters."""
        cls.enabled = data.get("enabled", cls.enabled)
        cls.schedule_type = data.get("schedule_type", cls.schedule_type)
        cls.selected_days = data.get("selected_days", cls.selected_days)
        cls.scheduled_hour = data.get("scheduled_hour", cls.scheduled_hour)
        cls.scheduled_minute = data.get("scheduled_minute", cls.scheduled_minute)
        
        # Adjust scheduler thread state to match updated configuration
        if cls.enabled:
            cls.start()
        else:
            cls.stop()

    @classmethod
    def _loop(cls):
        """Local scheduler ticking loop checking schedule match once per minute."""
        logger.info("Entering scheduler thread execution loop.")
        while not cls._stop_event.is_set():
            now = datetime.now()
            
            # Verify schedule matching constraints
            should_run = False
            
            if cls.schedule_type == "hourly":
                if now.minute == cls.scheduled_minute:
                    should_run = True
            elif cls.schedule_type == "daily":
                if now.hour == cls.scheduled_hour and now.minute == cls.scheduled_minute:
                    should_run = True
            elif cls.schedule_type == "selected_days":
                if now.weekday() in cls.selected_days:
                    if now.hour == cls.scheduled_hour and now.minute == cls.scheduled_minute:
                        should_run = True

            # Ensure we don't trigger multiple times in the same minute
            if should_run:
                if not cls.last_run_time or (now - cls.last_run_time).total_seconds() > 90:
                    cls.last_run_time = now
                    logger.info("Schedule criteria matches! Invoking automated JobPilotOrchestrator pipeline.")
                    cls._trigger_orchestration()

            # Sleep 10s between checks
            time.sleep(10)

    @classmethod
    def _trigger_orchestration(cls):
        """Runs the orchestrator asynchronously in a separate worker thread context."""
        from app.services.orchestration.orchestrator import JobPilotOrchestrator
        from app.models.mission import JobSearchMission
        from app.services.mission_engine import MissionEngine
        db = SessionLocal()
        try:
            # 1. Orchestrator default profile runs on profile_id = 1
            threading.Thread(
                target=JobPilotOrchestrator.run_pipeline,
                args=(db, 1, "SCHEDULED"),
                daemon=True
            ).start()

            # 2. Query and trigger active missions
            active_missions = db.query(JobSearchMission).filter(JobSearchMission.status == "ACTIVE").all()
            for mission in active_missions:
                threading.Thread(
                    target=MissionEngine.run_mission,
                    args=(db, mission.id, "SCHEDULED"),
                    daemon=True
                ).start()
                
        except Exception as e:
            logger.error(f"Failed to launch scheduled run: {e}")
        finally:
            db.close()


# Type hints import helper
from typing import Optional, List

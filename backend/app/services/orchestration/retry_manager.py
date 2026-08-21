import logging
from sqlalchemy.orm import Session
from app.models.application import Application, SubmissionRun

logger = logging.getLogger(__name__)


class RetryManager:
    """
    Manages retry logic, categorizes error types, and isolates recoverable vs non-recoverable failures.
    """

    RECOVERABLE_ERRORS = [
        "network",
        "connection",
        "timeout",
        "browser crashed",
        "navigation failed",
        "playwright error",
        "dns error",
        "proxy error",
        "rate limit reached"
    ]

    NON_RECOVERABLE_ERRORS = [
        "captcha",
        "login required",
        "authentication failed",
        "missing field",
        "validation error",
        "unauthorized",
        "domain validation",
        "blocked",
        "unverified",
        "duplicate"
    ]

    @classmethod
    def is_recoverable(cls, error_message: str) -> bool:
        """
        Determines if a failure is transient/recoverable.
        """
        if not error_message:
            return False
        
        err_lower = error_message.lower()
        
        # Check non-recoverable first (takes precedence)
        for non_rec in cls.NON_RECOVERABLE_ERRORS:
            if non_rec in err_lower:
                return False

        for rec in cls.RECOVERABLE_ERRORS:
            if rec in err_lower:
                return True

        # Default fallback to non-recoverable for safety
        return False

    @classmethod
    def should_retry_application(
        cls,
        db: Session,
        application_id: int,
        max_retries: int = 3
    ) -> bool:
        """
        Looks up past failed runs to decide if the application run should be retried.
        """
        failed_runs = db.query(SubmissionRun).filter(
            SubmissionRun.application_id == application_id,
            SubmissionRun.status == "FAILED"
        ).all()

        if len(failed_runs) >= max_retries:
            logger.info(f"Application {application_id} has exceeded max retries limit ({len(failed_runs)}/{max_retries}).")
            return False

        # Verify that all past failures were indeed recoverable
        for run in failed_runs:
            if run.error_message and not cls.is_recoverable(run.error_message):
                logger.info(f"Application {application_id} failed with non-recoverable error: {run.error_message}. Blocking retry.")
                return False

        return True

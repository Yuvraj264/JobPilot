import logging
import re
import json
from app.config import settings

class SensitiveDataRedactor(logging.Filter):
    """
    Logging filter redacting passwords, tokens, cookies, API keys, phone numbers,
    and email addresses from logs to prevent credentials leaking.
    """
    SENSITIVE_PATTERNS = [
        (re.compile(r'(?i)(password|token|secret|key|cookie|authorization|passwd)\s*[:=]\s*["\']?([^"\'\s&,;]+)["\']?'), r'\1: ********'),
        # Redact Bearer authorization header tokens
        (re.compile(r'(?i)Bearer\s+([^"\'\s]+)'), r'Bearer ********'),
        # Redact Email patterns
        (re.compile(r'[\w\.-]+@[\w\.-]+\.\w+'), r'********@example.com'),
        # Redact Phone numbers (international, US, simple formats)
        (re.compile(r'\b(?:\+?\d{1,3}[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b'), r'***-***-****'),
    ]

    def filter(self, record):
        if not isinstance(record.msg, str):
            record.msg = str(record.msg)

        msg = record.msg
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            msg = pattern.sub(replacement, msg)
        record.msg = msg
        return True


class StructuredJSONFormatter(logging.Formatter):
    """
    JSON Formatter for production environments log management.
    """
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", None),
            "application_id": getattr(record, "application_id", None),
            "source": getattr(record, "source", None),
            "error_code": getattr(record, "error_code", None)
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_structured_logging():
    """Sets up Python logging with redactors and JSON formatters."""
    root_logger = logging.getLogger()

    # Remove existing handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()

    # Add Sensitive Data Redactor Filter
    redactor = SensitiveDataRedactor()
    handler.addFilter(redactor)

    # Choose Formatter based on config
    if settings.LOG_FORMAT.lower() == "json":
        formatter = StructuredJSONFormatter()
    else:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.LOG_LEVEL.upper())

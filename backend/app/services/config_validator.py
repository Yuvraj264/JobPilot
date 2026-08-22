import os
import urllib.parse
from pathlib import Path
from app.config import Settings
from app.database.connection import check_db_connection

class ConfigurationValidator:
    """
    Configuration Validator checking required parameters, type constraints, writable storage,
    valid URL targets, and database availability at startup.
    Fails fast for invalid configurations in production.
    """

    @classmethod
    def validate_settings(cls, settings: Settings):
        issues = []

        # 1. Required Variables Checks
        if not settings.APP_NAME:
            issues.append("APP_NAME must be specified.")
        if not settings.DATABASE_URL:
            issues.append("DATABASE_URL must be specified.")
        if settings.APP_ENV == "production":
            if settings.SECRET_KEY in ["change-me-to-something-very-long-in-production!!!", ""]:
                issues.append("SECRET_KEY must be overridden with a secure value in production.")
            if len(settings.SECRET_KEY) < 32:
                issues.append("SECRET_KEY must be at least 32 characters long in production.")

        # 2. URL Validations
        db_url = settings.DATABASE_URL
        try:
            parsed_db = urllib.parse.urlparse(db_url)
            if parsed_db.scheme not in ["postgresql", "sqlite"]:
                issues.append(f"DATABASE_URL uses unsupported scheme '{parsed_db.scheme}'. Only postgresql and sqlite supported.")
        except Exception:
            issues.append("DATABASE_URL is not a syntactically valid URL.")

        for url in settings.cors_origins_list:
            if not url.startswith("http://") and not url.startswith("https://"):
                issues.append(f"CORS Origin URL '{url}' must start with http:// or https://.")

        # 3. Numeric Boundaries & Positive Limits
        if settings.MAX_RESUME_FILE_SIZE_MB <= 0:
            issues.append(f"MAX_RESUME_FILE_SIZE_MB must be positive, got {settings.MAX_RESUME_FILE_SIZE_MB}.")
        if settings.BROWSER_TIMEOUT_MS <= 0:
            issues.append(f"BROWSER_TIMEOUT_MS must be positive, got {settings.BROWSER_TIMEOUT_MS}.")
        if settings.API_RATE_LIMIT_PER_MINUTE <= 0:
            issues.append(f"API_RATE_LIMIT_PER_MINUTE must be positive, got {settings.API_RATE_LIMIT_PER_MINUTE}.")
        if settings.MAX_APPLICATIONS_PER_DAY <= 0:
            issues.append(f"MAX_APPLICATIONS_PER_DAY must be positive, got {settings.MAX_APPLICATIONS_PER_DAY}.")
        if settings.MAX_APPLICATIONS_PER_RUN <= 0:
            issues.append(f"MAX_APPLICATIONS_PER_RUN must be positive, got {settings.MAX_APPLICATIONS_PER_RUN}.")
        if settings.COOLDOWN_DAYS <= 0:
            issues.append(f"COOLDOWN_DAYS must be positive, got {settings.COOLDOWN_DAYS}.")

        # 4. Storage Directories Writable check
        try:
            storage_path = Path(settings.RESUME_STORAGE_PATH)
            storage_path.mkdir(parents=True, exist_ok=True)
            test_file = storage_path / ".write_test"
            test_file.write_text("write_ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
        except Exception as e:
            issues.append(f"RESUME_STORAGE_PATH '{settings.RESUME_STORAGE_PATH}' is not writable: {str(e)}")

        # Fail fast if there are critical issues
        if issues:
            redacted_issues = [cls.redact_secrets(issue, settings) for issue in issues]
            raise ValueError(f"CRITICAL CONFIGURATION ERROR:\n- " + "\n- ".join(redacted_issues))

        # 5. Database Connection verification (Only if not in sqlite-memory test mode)
        if settings.APP_ENV == "production" or not settings.DATABASE_URL.startswith("sqlite://"):
            db_res = check_db_connection()
            if db_res.get("status") != "connected":
                raise ConnectionError(f"CRITICAL DATABASE CONNECTION ERROR: {cls.redact_secrets(db_res.get('error', 'Unknown database connection error'), settings)}")

    @classmethod
    def redact_secrets(cls, text: str, settings: Settings) -> str:
        """Redacts sensitive values like database passwords or keys from log messages."""
        if not text:
            return ""
        # Redact DATABASE_URL passwords
        if settings.DATABASE_URL:
            try:
                parsed = urllib.parse.urlparse(settings.DATABASE_URL)
                if parsed.password:
                    text = text.replace(parsed.password, "********")
            except Exception:
                pass
        # Redact SECRET_KEY
        if settings.SECRET_KEY:
            text = text.replace(settings.SECRET_KEY, "********")
        # Redact API Keys
        if settings.AI_API_KEY:
            text = text.replace(settings.AI_API_KEY, "********")
        return text

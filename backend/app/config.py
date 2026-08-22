import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized JobPilot Application Settings.
    Loaded from environment variables with safe defaults for local development.
    """
    # General
    APP_NAME: str = "JobPilot"
    APP_ENV: str = "development"  # development, test, production
    DEBUG: bool = True
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

    # DATABASE Category
    DATABASE_URL: str = "postgresql://jobpilot:jobpilot_dev_password@localhost:5433/jobpilot_db"

    # STORAGE Category
    RESUME_STORAGE_PATH: str = "./storage/resumes"
    MAX_RESUME_FILE_SIZE_MB: int = 10

    # BROWSER Category
    PLAYWRIGHT_HEADLESS: bool = True
    BROWSER_TIMEOUT_MS: int = 30000

    # AI Category
    AI_PROVIDER: str = "mock"  # mock, openai, anthropic
    AI_API_KEY: str = ""
    AI_MODEL_NAME: str = "gpt-4o"

    # JOB SOURCES Category
    JOB_SOURCES_DISCOVERY_LIMIT: int = 20
    JOB_SOURCES_RATE_LIMIT_DELAY: int = 2

    # APPLICATION SOURCES Category
    ALLOWED_APPLICATION_DOMAINS: str = "localhost,127.0.0.1,greenhouse.io,lever.co"

    # SCHEDULER Category
    SCHEDULER_CHECK_INTERVAL_SECONDS: int = 60
    SCHEDULER_HEARTBEAT_FILE: str = "./storage/scheduler_heartbeat.json"

    # SECURITY Category
    API_RATE_LIMIT_PER_MINUTE: int = 60
    SECRET_KEY: str = "change-me-to-something-very-long-in-production!!!"
    ALLOW_LOCAL_URLS_FOR_DEV: bool = True

    # LOGGING Category
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "text"  # text, json

    # LIMITS Category
    MAX_APPLICATIONS_PER_DAY: int = 10
    MAX_APPLICATIONS_PER_RUN: int = 3
    COOLDOWN_DAYS: int = 30

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_domains_list(self) -> List[str]:
        return [domain.strip() for domain in self.ALLOWED_APPLICATION_DOMAINS.split(",") if domain.strip()]

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Global settings instance
settings = Settings()


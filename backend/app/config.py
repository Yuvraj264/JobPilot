import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized JobPilot Application Settings.
    Loaded from environment variables with safe defaults for local development.
    """
    APP_NAME: str = "JobPilot"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    
    # Database Settings
    DATABASE_URL: str = "postgresql://jobpilot:jobpilot_dev_password@localhost:5433/jobpilot_db"
    
    # Resume Storage Settings
    RESUME_STORAGE_PATH: str = "./storage/resumes"
    MAX_RESUME_FILE_SIZE_MB: int = 10
    
    # CORS Origins (parsed as list if comma separated string)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

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

from app.api.profile_routes import router as profile_router
from app.api.resume_routes import router as resume_router
from app.api.job_routes import router as job_router
from app.api.matching_routes import router as matching_router
from app.api.automation_routes import router as automation_router
from app.api.mock_app_routes import router as mock_app_router
from app.api.screening_routes import router as screening_router
from app.api.tailoring_routes import router as tailoring_router
from app.api.application_routes import router as application_router

__all__ = [
    "profile_router",
    "resume_router",
    "job_router",
    "matching_router",
    "automation_router",
    "mock_app_router",
    "screening_router",
    "tailoring_router",
    "application_router",
]

from app.api.profile_routes import router as profile_router
from app.api.resume_routes import router as resume_router
from app.api.job_routes import router as job_router
from app.api.matching_routes import router as matching_router

__all__ = ["profile_router", "resume_router", "job_router", "matching_router"]

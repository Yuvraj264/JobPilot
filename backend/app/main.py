from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import check_db_connection

from app.api.profile_routes import router as profile_router
from app.api.resume_routes import router as resume_router
from app.api.job_routes import router as job_router
from app.api.matching_routes import router as matching_router
from app.api.automation_routes import router as automation_router
from app.api.mock_app_routes import router as mock_app_router

app = FastAPI(
    title=settings.APP_NAME,
    description="JobPilot AI-assisted job application automation platform backend API.",
    version="0.6.0",
    debug=settings.DEBUG,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(job_router)
app.include_router(matching_router)
app.include_router(automation_router)
app.include_router(mock_app_router)


@app.get("/", tags=["General"])
def read_root():
    """
    Root endpoint returning basic project details.
    """
    return {
        "name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "status": "running",
        "phase": "Phase 6 - Mock Application Environment & Application Agent Foundation",
        "docs_url": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint returning application & database connectivity status.
    """
    db_status = check_db_connection()
    is_healthy = db_status.get("status") == "connected"
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "database": db_status,
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }

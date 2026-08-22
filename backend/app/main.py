from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import check_db_connection
from app.services.logging_config import setup_structured_logging

setup_structured_logging()

from app.api.profile_routes import router as profile_router
from app.api.resume_routes import router as resume_router
from app.api.job_routes import router as job_router
from app.api.matching_routes import router as matching_router
from app.api.automation_routes import router as automation_router
from app.api.mock_app_routes import router as mock_app_router
from app.api.screening_routes import router as screening_router
from app.api.tailoring_routes import router as tailoring_router
from app.api.application_routes import router as application_router
from app.api.orchestration_routes import router as orchestration_router
from app.api.demo_routes import router as demo_router
from app.api.personalization_routes import router as personalization_router

app = FastAPI(
    title=settings.APP_NAME,
    description="JobPilot AI-assisted job application automation platform backend API.",
    version="0.12.0",
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

from app.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

@app.on_event("startup")
def startup_validation():
    # 1. Validate configuration settings
    from app.services.config_validator import ConfigurationValidator
    ConfigurationValidator.validate_settings(settings)

    # 1.5. Ensure all tables are created (including newly added models)
    from app.database.connection import engine, Base
    import app.models
    Base.metadata.create_all(bind=engine)

    # 2. Run database crash recovery checks
    from app.database.connection import SessionLocal
    from app.services.orchestration.orchestrator import JobPilotOrchestrator
    db = SessionLocal()
    try:
        JobPilotOrchestrator.recover_interrupted_runs(db)
    finally:
        db.close()

    # 3. Register signal handlers for graceful shutdown
    import signal
    import sys
    import logging
    import threading
    logger = logging.getLogger("app.main")

    def signal_handler(signum, frame):
        logger.info(f"Received shutdown signal ({signum}). Performing graceful cleanup...")
        sys.exit(0)

    if threading.current_thread() is threading.main_thread():
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except ValueError:
            pass

app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(job_router)
app.include_router(matching_router)
app.include_router(automation_router)
app.include_router(mock_app_router)
app.include_router(screening_router)
app.include_router(tailoring_router)
app.include_router(application_router)
app.include_router(orchestration_router)
app.include_router(demo_router)
app.include_router(personalization_router)


@app.get("/", tags=["General"])
def read_root():
    """
    Root endpoint returning basic project details.
    """
    return {
        "name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "status": "running",
        "phase": "Phase 12 - Autonomous Job Application Orchestration, Scheduling, Monitoring & Analytics",
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


@app.get("/health/live", tags=["Health"])
def health_live():
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
def health_ready():
    db_status = check_db_connection()
    db_ok = db_status.get("status") == "connected"
    
    # Check if storage is writable
    storage_ok = False
    try:
        os.makedirs(settings.RESUME_STORAGE_PATH, exist_ok=True)
        test_file = os.path.join(settings.RESUME_STORAGE_PATH, ".health_test")
        with open(test_file, "w") as f:
            f.write("ready")
        os.remove(test_file)
        storage_ok = True
    except Exception:
        pass
        
    if db_ok and storage_ok:
        return {"status": "ready"}
    else:
        return {
            "status": "not_ready",
            "database": "ok" if db_ok else "failed",
            "storage": "ok" if storage_ok else "failed"
        }


@app.get("/health/database", tags=["Health"])
def health_database():
    return check_db_connection()


@app.get("/health/browser", tags=["Health"])
def health_browser():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return {"status": "healthy", "browser": "playwright_chromium_available"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/health/scheduler", tags=["Health"])
def health_scheduler():
    # Check if heartbeat file was updated recently (last 2 minutes)
    hb_file = settings.SCHEDULER_HEARTBEAT_FILE
    if os.path.exists(hb_file):
        mtime = os.path.getmtime(hb_file)
        import time
        if time.time() - mtime < 120:
            return {"status": "healthy", "last_heartbeat": mtime}
    return {"status": "unhealthy", "reason": "No active scheduler heartbeat."}


@app.get("/health/sources", tags=["Health"])
def health_sources():
    from app.services.automation.adapters.registry import registry
    adapters = registry.list()
    statuses = {a.name(): "available" for a in adapters}
    return {"status": "healthy", "adapters": statuses}


@app.get("/api/metrics", tags=["Metrics"])
def get_metrics():
    from fastapi.responses import PlainTextResponse
    from app.services.observability_service import ObservabilityService
    return PlainTextResponse(content=ObservabilityService.get_metrics_prometheus())


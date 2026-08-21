from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database.connection import get_db
from app.models.job import JobSource, Job, JobDiscoveryRun
from app.services.adapters.registry import registry
from app.services.job_discovery_service import JobDiscoveryService
from app.schemas.job import (
    JobSourceResponse,
    JobResponse,
    JobDetailResponse,
    JobStatusUpdate,
    JobDiscoveryRunResponse,
    JobStatsResponse,
    DiscoverySummaryResponse,
)

router = APIRouter(prefix="/api/jobs", tags=["Job Discovery & Ingestion"])


@router.get("/sources", response_model=List[JobSourceResponse])
def list_job_sources(db: Session = Depends(get_db)):
    """List all registered job sources and their configuration state."""
    # Ensure all registered adapters exist in database
    for adapter in registry.list_adapters():
        JobDiscoveryService.sync_job_source_record(db, adapter)
    return db.query(JobSource).order_by(JobSource.id.asc()).all()


@router.get("/sources/{source_name}", response_model=JobSourceResponse)
def get_job_source(source_name: str, db: Session = Depends(get_db)):
    """Get metadata for a specific job source."""
    source = db.query(JobSource).filter(JobSource.name == source_name.lower()).first()
    if not source:
        adapter = registry.get(source_name)
        if adapter:
            return JobDiscoveryService.sync_job_source_record(db, adapter)
        raise HTTPException(status_code=404, detail=f"Job source '{source_name}' not found.")
    return source


@router.post("/sources/{source_name}/enable", response_model=JobSourceResponse)
def enable_job_source(source_name: str, db: Session = Depends(get_db)):
    """Enable target job source."""
    registry.enable(source_name)
    source = db.query(JobSource).filter(JobSource.name == source_name.lower()).first()
    if not source:
        adapter = registry.get(source_name)
        if not adapter:
            raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found.")
        source = JobDiscoveryService.sync_job_source_record(db, adapter)
    source.enabled = True
    db.commit()
    db.refresh(source)
    return source


@router.post("/sources/{source_name}/disable", response_model=JobSourceResponse)
def disable_job_source(source_name: str, db: Session = Depends(get_db)):
    """Disable target job source."""
    registry.disable(source_name)
    source = db.query(JobSource).filter(JobSource.name == source_name.lower()).first()
    if not source:
        adapter = registry.get(source_name)
        if not adapter:
            raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found.")
        source = JobDiscoveryService.sync_job_source_record(db, adapter)
    source.enabled = False
    db.commit()
    db.refresh(source)
    return source


@router.post("/discover", response_model=List[DiscoverySummaryResponse])
def discover_all_jobs(limit_per_source: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Trigger job discovery across all enabled registered job sources."""
    results = JobDiscoveryService.run_discovery_all_enabled(db, limit_per_source=limit_per_source)
    return results


@router.post("/discover/{source_name}", response_model=DiscoverySummaryResponse)
def discover_jobs_from_source(source_name: str, limit: int = Query(50, ge=1, le=200), page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    """Trigger job discovery for a specific source adapter."""
    adapter = registry.get(source_name)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Adapter for source '{source_name}' not registered.")

    try:
        summary = JobDiscoveryService.run_discovery_for_source(db, adapter, limit=limit, page=page)
        return summary
    except NotImplementedError as nie:
        raise HTTPException(status_code=501, detail=str(nie))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(err)}")


@router.get("/stats", response_model=JobStatsResponse)
def get_job_stats(db: Session = Depends(get_db)):
    """Get job discovery and catalog statistics."""
    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.status == "ACTIVE").count()
    duplicate_jobs = db.query(Job).filter(Job.status == "DUPLICATE").count()
    potential_duplicates = db.query(Job).filter(Job.status == "POTENTIAL_DUPLICATE").count()
    
    total_sources = db.query(JobSource).count()
    enabled_sources = db.query(JobSource).filter(JobSource.enabled == True).count()

    today_start = datetime.combine(date.today(), datetime.min.time())
    jobs_today = db.query(Job).filter(Job.discovered_at >= today_start).count()

    return {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs + db.query(Job).filter(Job.status == "DISCOVERED").count(),
        "duplicate_jobs": duplicate_jobs,
        "potential_duplicates": potential_duplicates,
        "total_sources": total_sources,
        "enabled_sources": enabled_sources,
        "jobs_discovered_today": jobs_today,
    }


@router.get("/discovery-runs", response_model=List[JobDiscoveryRunResponse])
def list_discovery_runs(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    """Retrieve historical discovery execution audit logs."""
    return db.query(JobDiscoveryRun).order_by(JobDiscoveryRun.started_at.desc()).limit(limit).all()


@router.get("/search", response_model=List[JobResponse])
def search_jobs(
    q: str = Query(..., min_length=1, description="Keyword search query"),
    company: Optional[str] = None,
    location: Optional[str] = None,
    workplace_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Deterministic keyword search across title, company_name, and description."""
    query = db.query(Job)
    
    keyword_filter = or_(
        Job.title.ilike(f"%{q}%"),
        Job.company_name.ilike(f"%{q}%"),
        Job.description.ilike(f"%{q}%"),
    )
    query = query.filter(keyword_filter)

    if company:
        query = query.filter(Job.company_name.ilike(f"%{company}%"))
    if location:
        query = query.filter(or_(Job.location.ilike(f"%{location}%"), Job.normalized_location.ilike(f"%{location}%")))
    if workplace_type:
        query = query.filter(Job.workplace_type == workplace_type.upper())

    return query.order_by(Job.discovered_at.desc()).offset(offset).limit(limit).all()


@router.get("", response_model=List[JobResponse])
def list_jobs(
    title: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    source_id: Optional[int] = None,
    employment_type: Optional[str] = None,
    workplace_type: Optional[str] = None,
    job_status: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List jobs with structured filters and pagination."""
    query = db.query(Job)

    if title:
        query = query.filter(Job.title.ilike(f"%{title}%"))
    if company:
        query = query.filter(Job.company_name.ilike(f"%{company}%"))
    if location:
        query = query.filter(or_(Job.location.ilike(f"%{location}%"), Job.normalized_location.ilike(f"%{location}%")))
    if source_id:
        query = query.filter(Job.source_id == source_id)
    if employment_type:
        query = query.filter(Job.employment_type == employment_type.upper())
    if workplace_type:
        query = query.filter(Job.workplace_type == workplace_type.upper())
    if job_status:
        query = query.filter(Job.status == job_status.upper())

    return query.order_by(Job.discovered_at.desc()).offset(offset).limit(limit).all()


@router.get("/{id}", response_model=JobDetailResponse)
def get_job(id: int, db: Session = Depends(get_db)):
    """Retrieve detailed job information by ID."""
    job = db.query(Job).filter(Job.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {id} not found.")
    return job


@router.patch("/{id}/status", response_model=JobResponse)
def update_job_status(id: int, payload: JobStatusUpdate, db: Session = Depends(get_db)):
    """Update job status (ACTIVE, EXPIRED, CLOSED, SKIPPED, etc.)."""
    job = db.query(Job).filter(Job.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {id} not found.")
    job.status = payload.status.upper()
    db.commit()
    db.refresh(job)
    return job

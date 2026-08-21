from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.profile_service import ProfileService
from app.services.application.validation_service import ApplicationValidationService
from app.services.application.approval_service import ApplicationApprovalService
from app.services.application.authorization_service import SubmissionAuthorizationService
from app.services.application.audit_service import ApplicationAuditService
from app.services.submission.submission_engine import SubmissionEngine
from app.models.job import Job
from app.models.matching import JobMatch
from app.models.tailoring import ApplicationPackage, TailoredResume
from app.models.resume import Resume
from app.models.application import (
    Application,
    PackageVersion,
    SubmissionAuthorization,
    SubmissionRun,
    ApplicationAuditLog,
    ApplicationSourceConfiguration,
    HumanInterventionEvent,
    ApplicationQueue,
)
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationApprovalRequest,
    ApplicationRejectRequest,
    ApplicationRequestChangesRequest,
    SubmissionAuthorizationResponse,
    SubmissionRunResponse,
    ApplicationTimelineResponse,
    ApplicationSourceConfigurationResponse,
    ApplicationSourceConfigurationUpdate,
    HumanInterventionEventResponse,
    ApplicationQueueResponse,
    BrowserStateResponse,
)
from app.services.automation.adapters.registry import registry
from app.services.automation.execution_worker import ApplicationExecutionWorker
from datetime import datetime

router = APIRouter(tags=["Application & Submission Control Layer"])


@router.post("/api/applications", response_model=ApplicationResponse)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    """Create a new Application tracking record."""
    profile = ProfileService.get_profile(db, user_id=1)
    if not profile:
        from app.services.seed_service import seed_sample_profile
        profile = seed_sample_profile(db, user_id=1)

    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {payload.job_id} not found.")

    match = db.query(JobMatch).filter(JobMatch.job_id == payload.job_id, JobMatch.profile_id == profile.id).first()

    pkg = None
    if payload.application_package_id:
        pkg = db.query(ApplicationPackage).filter(ApplicationPackage.id == payload.application_package_id).first()

    app_rec = Application(
        profile_id=profile.id,
        job_id=job.id,
        match_id=match.id if match else None,
        application_package_id=pkg.id if pkg else None,
        selected_resume_id=payload.source_resume_id,
        tailored_resume_id=payload.tailored_resume_id,
        status="PREPARING",
        source="MOCK_PLATFORM",
        application_url=job.application_url or job.job_url
    )
    db.add(app_rec)
    db.commit()
    db.refresh(app_rec)

    # Initialize Package Version 1 if package exists
    if pkg:
        ver = PackageVersion(
            application_package_id=pkg.id,
            version=1,
            package_content={"job_id": job.id, "status": "CREATED"},
            created_by="SYSTEM"
        )
        db.add(ver)
        db.commit()

    ApplicationAuditService.log_event(db, app_rec.id, "APPLICATION_CREATED", "SYSTEM", {"job_id": job.id})
    return app_rec


@router.get("/api/applications", response_model=List[ApplicationResponse])
def list_applications(db: Session = Depends(get_db)):
    """List all application control records."""
    return db.query(Application).order_by(Application.created_at.desc()).all()


@router.get("/api/applications/{id}", response_model=ApplicationResponse)
def get_application(id: int, db: Session = Depends(get_db)):
    """Retrieve single application control record."""
    app_rec = db.query(Application).filter(Application.id == id).first()
    if not app_rec:
        raise HTTPException(status_code=404, detail=f"Application {id} not found.")
    return app_rec


@router.get("/api/applications/{id}/timeline", response_model=ApplicationTimelineResponse)
def get_application_timeline(id: int, db: Session = Depends(get_db)):
    """Retrieve human-readable chronological event timeline."""
    app_rec = db.query(Application).filter(Application.id == id).first()
    if not app_rec:
        raise HTTPException(status_code=404, detail=f"Application {id} not found.")

    timeline = ApplicationAuditService.get_timeline(db, id)
    return {"application_id": id, "timeline": timeline}


@router.post("/api/applications/{id}/validate")
def validate_application(id: int, db: Session = Depends(get_db)):
    """Run Application Validation Pipeline."""
    app_rec = db.query(Application).filter(Application.id == id).first()
    if not app_rec:
        raise HTTPException(status_code=404, detail=f"Application {id} not found.")

    res = ApplicationValidationService.validate_application(
        db, app_rec.job, app_rec.profile, app_rec.selected_resume, app_rec.tailored_resume, app_rec.package
    )
    ApplicationAuditService.log_event(db, id, "VALIDATION_RUN", "SYSTEM", res)
    return res


@router.post("/api/applications/{id}/review", response_model=ApplicationResponse)
def request_application_review(id: int, db: Session = Depends(get_db)):
    """Request human review for application (transitions to READY_FOR_REVIEW if validation passes)."""
    try:
        return ApplicationApprovalService.request_review(db, id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/api/applications/{id}/approve", response_model=ApplicationResponse)
def approve_application(id: int, payload: ApplicationApprovalRequest, db: Session = Depends(get_db)):
    """Explicitly approve application for submission."""
    try:
        return ApplicationApprovalService.approve_application(
            db, id, user_confirmed=payload.user_confirmed, notes=payload.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/applications/{id}/reject", response_model=ApplicationResponse)
def reject_application(id: int, payload: ApplicationRejectRequest, db: Session = Depends(get_db)):
    """Reject application."""
    try:
        return ApplicationApprovalService.reject_application(db, id, rejection_reason=payload.rejection_reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/applications/{id}/request-changes", response_model=ApplicationResponse)
def request_changes_for_application(id: int, payload: ApplicationRequestChangesRequest, db: Session = Depends(get_db)):
    """Request changes for application."""
    try:
        return ApplicationApprovalService.request_changes(db, id, change_instructions=payload.change_instructions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/applications/{id}/authorize-submission", response_model=SubmissionAuthorizationResponse)
def authorize_submission(id: int, db: Session = Depends(get_db)):
    """Issue submission authorization token for an APPROVED application."""
    try:
        auth = SubmissionAuthorizationService.authorize_submission(db, id)
        return auth
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post("/api/applications/{id}/revoke-authorization", response_model=ApplicationResponse)
def revoke_submission_authorization(id: int, db: Session = Depends(get_db)):
    """Revoke active submission authorization."""
    try:
        return SubmissionAuthorizationService.revoke_authorization(db, id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/applications/{id}/submit")
def submit_application(id: int, trigger_mock_captcha: bool = Query(False), db: Session = Depends(get_db)):
    """Execute submission engine for authorized application."""
    try:
        res = SubmissionEngine.execute_submission(db, id, trigger_mock_captcha=trigger_mock_captcha)
        return res
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/api/applications/{id}/submission", response_model=List[SubmissionRunResponse])
def get_submission_runs(id: int, db: Session = Depends(get_db)):
    """List submission execution runs for application."""
    return db.query(SubmissionRun).filter(SubmissionRun.application_id == id).order_by(SubmissionRun.started_at.desc()).all()


@router.get("/api/applications/{id}/audit")
def get_audit_logs(id: int, db: Session = Depends(get_db)):
    """Get raw audit logs for application."""
    return db.query(ApplicationAuditLog).filter(ApplicationAuditLog.application_id == id).order_by(ApplicationAuditLog.timestamp.desc()).all()


@router.get("/api/application-sources", response_model=List[ApplicationSourceConfigurationResponse])
def get_application_sources(db: Session = Depends(get_db)):
    """List all configured application source setups."""
    configs = []
    for adapter in registry.list():
        cfg = ApplicationExecutionWorker.get_or_create_source_config(db, adapter.name())
        configs.append(cfg)
    return configs


@router.get("/api/application-sources/{source}", response_model=ApplicationSourceConfigurationResponse)
def get_application_source_config(source: str, db: Session = Depends(get_db)):
    """Get configuration details for a source."""
    adapter = registry.get(source)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source adapter '{source}' not found.")
    return ApplicationExecutionWorker.get_or_create_source_config(db, adapter.name())


@router.post("/api/application-sources/{source}/test")
def test_application_source(source: str, db: Session = Depends(get_db)):
    """Perform health check / test capabilities on adapter."""
    adapter = registry.get(source)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source adapter '{source}' not found.")
    capabilities = adapter.get_capabilities()
    return {"source": source, "health": "healthy", "capabilities": capabilities}


@router.post("/api/applications/{id}/prepare", response_model=ApplicationQueueResponse)
def prepare_application_run(id: int, db: Session = Depends(get_db)):
    """Prepares/Enqueues an approved application into ApplicationQueue."""
    app_rec = db.query(Application).filter(Application.id == id).first()
    if not app_rec:
        raise HTTPException(status_code=404, detail=f"Application {id} not found.")
        
    if app_rec.status not in ["APPROVED", "SUBMISSION_AUTHORIZED", "SUBMITTING", "PREPARING"]:
        raise HTTPException(status_code=400, detail="Only APPROVED or PREPARING applications can be queued.")
        
    queue_rec = db.query(ApplicationQueue).filter(ApplicationQueue.application_id == id).first()
    if not queue_rec:
        queue_rec = ApplicationQueue(
            application_id=id,
            priority=1.0,
            status="QUEUED"
        )
        db.add(queue_rec)
        db.commit()
        db.refresh(queue_rec)
    else:
        queue_rec.status = "QUEUED"
        queue_rec.queued_at = datetime.now()
        queue_rec.started_at = None
        queue_rec.completed_at = None
        db.commit()
        db.refresh(queue_rec)
        
    ApplicationAuditService.log_event(db, id, "APPLICATION_QUEUED", "SYSTEM", {"priority": queue_rec.priority})
    return queue_rec


@router.post("/api/applications/{id}/execute")
def execute_application_run(id: int, db: Session = Depends(get_db)):
    """Run worker execution synchronously/immediately on the queued application (dry_run = False)."""
    res = ApplicationExecutionWorker.execute_queued_application(db, id, dry_run=False)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error") or res.get("reason"))
    return res


@router.post("/api/applications/{id}/dry-run")
def dry_run_application_run(id: int, db: Session = Depends(get_db)):
    """Run worker execution immediately on the queued application (dry_run = True)."""
    res = ApplicationExecutionWorker.execute_queued_application(db, id, dry_run=True)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error") or res.get("reason"))
    return res


@router.post("/api/applications/{id}/resume")
def resume_application_run(id: int, db: Session = Depends(get_db)):
    """Resolves the active HumanInterventionEvent, marks intervention resolved, and resumes run."""
    app_rec = db.query(Application).filter(Application.id == id).first()
    if not app_rec:
        raise HTTPException(status_code=404, detail=f"Application {id} not found.")
        
    if app_rec.status != "PAUSED":
        raise HTTPException(status_code=400, detail=f"Cannot resume application in status '{app_rec.status}'.")
        
    active_event = db.query(HumanInterventionEvent).filter(
        HumanInterventionEvent.application_id == id,
        HumanInterventionEvent.resolution == None
    ).first()
    
    if active_event:
        active_event.resolved_at = datetime.now()
        active_event.resolution = "RESOLVED"
        active_event.notes = "Manually resolved by user."
        db.commit()
        
    app_rec.status = "APPROVED"
    db.commit()
    
    ApplicationAuditService.log_event(db, id, "APPLICATION_RESUMED", "SYSTEM", {})
    return {"success": True, "message": "Intervention resolved. Status reset to APPROVED."}


@router.post("/api/applications/{id}/cancel")
def cancel_application_run(id: int, db: Session = Depends(get_db)):
    """Removes application from queue, transitions status to CHANGES_REQUESTED."""
    app_rec = db.query(Application).filter(Application.id == id).first()
    if not app_rec:
        raise HTTPException(status_code=404, detail=f"Application {id} not found.")
        
    queue_rec = db.query(ApplicationQueue).filter(ApplicationQueue.application_id == id).first()
    if queue_rec:
        queue_rec.status = "CANCELLED"
        queue_rec.completed_at = datetime.now()
        db.commit()
        
    app_rec.status = "CHANGES_REQUESTED"
    db.commit()
    
    ApplicationAuditService.log_event(db, id, "APPLICATION_CANCELLED", "SYSTEM", {})
    return {"success": True, "message": "Application execution run cancelled."}


@router.get("/api/applications/{id}/action-plan")
def get_application_action_plan(id: int, db: Session = Depends(get_db)):
    """Previews action plan using profile field mapping without submitting."""
    app_rec = db.query(Application).filter(Application.id == id).first()
    if not app_rec:
        raise HTTPException(status_code=404, detail=f"Application {id} not found.")
        
    from app.services.automation.profile_field_mapper import ProfileFieldMapper
    
    default_resume = db.query(Resume).filter(Resume.id == app_rec.selected_resume_id).first()
    if not default_resume:
        default_resume = db.query(Resume).filter(Resume.profile_id == app_rec.profile_id).first()
        
    preview_fields = ["EMAIL", "FULL_NAME", "PHONE", "RESUME", "WEBSITE"]
    plan_list = []
    for idx, f in enumerate(preview_fields):
        mapping = ProfileFieldMapper.map_field(f, app_rec.profile, default_resume)
        plan_list.append({
            "step_number": idx + 1,
            "field_type": f,
            "value": "********" if f == "PASSWORD" else str(mapping["value"]),
            "confidence": mapping["confidence"],
            "action": "UPLOAD" if f == "RESUME" else "FILL"
        })
    return {"application_id": id, "plan": plan_list}


@router.get("/api/applications/{id}/interventions", response_model=List[HumanInterventionEventResponse])
def get_application_interventions(id: int, db: Session = Depends(get_db)):
    """Returns list of historical HumanInterventionEvent records for the application."""
    return db.query(HumanInterventionEvent).filter(HumanInterventionEvent.application_id == id).order_by(HumanInterventionEvent.created_at.desc()).all()


@router.get("/api/applications/{id}/browser-state", response_model=BrowserStateResponse)
def get_application_browser_state(id: int, db: Session = Depends(get_db)):
    """Returns current screenshot list, url, title, state."""
    from app.models.automation import AutomationRun
    run = db.query(AutomationRun).filter(AutomationRun.profile_id == 1).order_by(AutomationRun.started_at.desc()).first()
    if not run:
        return {
            "application_id": id,
            "current_url": "",
            "page_title": "Not Started",
            "screenshots": [],
            "state": "NOT_STARTED"
        }
    return {
        "application_id": id,
        "current_url": run.current_url,
        "page_title": f"Application State: {run.state}",
        "screenshots": run.screenshots or [],
        "state": run.state
    }

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
from app.models.application import (
    Application,
    PackageVersion,
    SubmissionAuthorization,
    SubmissionRun,
    ApplicationAuditLog,
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
)

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

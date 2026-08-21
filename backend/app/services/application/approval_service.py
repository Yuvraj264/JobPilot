from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.application import (
    Application,
    ApplicationApproval,
    PackageVersion,
)
from app.models.tailoring import ApplicationPackage
from app.services.application.validation_service import ApplicationValidationService
from app.services.application.audit_service import ApplicationAuditService


class ApplicationApprovalService:
    """
    Application Approval Service managing human review requests, explicit user approvals,
    rejections, change requests, answer edits, and package versioning.
    """

    @staticmethod
    def request_review(db: Session, application_id: int) -> Application:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        # Run Validation Pipeline
        val = ApplicationValidationService.validate_application(
            db, app.job, app.profile, app.selected_resume, app.tailored_resume, app.package
        )
        if not val["valid"]:
            raise ValueError(f"Cannot request review: Blocking validation issues exist: {', '.join(val['blocking_issues'])}")

        app.status = "READY_FOR_REVIEW"
        
        # Record pending approval request
        approval = ApplicationApproval(
            application_id=app.id,
            package_version=app.package.versions[0].version if app.package and app.package.versions else 1,
            status="PENDING",
            requested_at=datetime.now()
        )
        db.add(approval)
        db.commit()

        ApplicationAuditService.log_event(db, app.id, "REVIEW_REQUESTED", "SYSTEM", {"status": "READY_FOR_REVIEW"})
        db.refresh(app)
        return app

    @staticmethod
    def approve_application(
        db: Session,
        application_id: int,
        user_confirmed: bool = False,
        reviewer: str = "HUMAN_USER",
        notes: Optional[str] = None
    ) -> Application:
        if not user_confirmed:
            raise ValueError("EXPLICIT CONFIRMATION REQUIRED: User must explicitly confirm review before approving.")

        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        val = ApplicationValidationService.validate_application(
            db, app.job, app.profile, app.selected_resume, app.tailored_resume, app.package
        )
        if not val["valid"]:
            raise ValueError(f"Approval blocked by validation issues: {', '.join(val['blocking_issues'])}")

        current_ver = app.package.versions[0].version if app.package and app.package.versions else 1

        app.status = "APPROVED"
        app.approved_at = datetime.now()

        # Update approval record
        approval = (
            db.query(ApplicationApproval)
            .filter(ApplicationApproval.application_id == app.id)
            .order_by(ApplicationApproval.requested_at.desc())
            .first()
        )
        if approval:
            approval.status = "APPROVED"
            approval.reviewed_at = datetime.now()
            approval.reviewer = reviewer
            approval.notes = notes

        # Mark package version approved
        if app.package and app.package.versions:
            app.package.versions[0].approved = True

        db.commit()
        ApplicationAuditService.log_event(db, app.id, "APPLICATION_APPROVED", reviewer, {"version": current_ver, "notes": notes})
        db.refresh(app)
        return app

    @staticmethod
    def reject_application(
        db: Session,
        application_id: int,
        rejection_reason: str,
        reviewer: str = "HUMAN_USER"
    ) -> Application:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        app.status = "REJECTED"
        app.rejected_at = datetime.now()

        approval = (
            db.query(ApplicationApproval)
            .filter(ApplicationApproval.application_id == app.id)
            .order_by(ApplicationApproval.requested_at.desc())
            .first()
        )
        if approval:
            approval.status = "REJECTED"
            approval.reviewed_at = datetime.now()
            approval.reviewer = reviewer
            approval.rejection_reason = rejection_reason

        db.commit()
        ApplicationAuditService.log_event(db, app.id, "APPLICATION_REJECTED", reviewer, {"reason": rejection_reason})
        db.refresh(app)
        return app

    @staticmethod
    def request_changes(
        db: Session,
        application_id: int,
        change_instructions: str,
        reviewer: str = "HUMAN_USER"
    ) -> Application:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        app.status = "CHANGES_REQUESTED"

        approval = (
            db.query(ApplicationApproval)
            .filter(ApplicationApproval.application_id == app.id)
            .order_by(ApplicationApproval.requested_at.desc())
            .first()
        )
        if approval:
            approval.status = "CHANGES_REQUESTED"
            approval.reviewed_at = datetime.now()
            approval.reviewer = reviewer
            approval.notes = change_instructions

        db.commit()
        ApplicationAuditService.log_event(db, app.id, "CHANGES_REQUESTED", reviewer, {"instructions": change_instructions})
        db.refresh(app)
        return app

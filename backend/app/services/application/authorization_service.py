from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.application import (
    Application,
    SubmissionAuthorization,
)
from app.services.application.validation_service import ApplicationValidationService
from app.services.application.audit_service import ApplicationAuditService


class SubmissionAuthorizationService:
    """
    Submission Authorization Service managing access tokens tied strictly to approved package versions.
    Enforces authorization rules (approved status, unexpired, unrevoked, unused, exact package version).
    """

    @staticmethod
    def authorize_submission(
        db: Session,
        application_id: int,
        authorized_by: str = "HUMAN_USER",
        duration_minutes: int = 60
    ) -> SubmissionAuthorization:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        # Rule 1: Application must be in APPROVED status
        if app.status != "APPROVED":
            raise ValueError(f"AUTHORIZATION FAILED: Application status is '{app.status}', expected 'APPROVED'.")

        # Rule 2: Validation check must pass cleanly
        val = ApplicationValidationService.validate_application(
            db, app.job, app.profile, app.selected_resume, app.tailored_resume, app.package
        )
        if not val["valid"]:
            raise ValueError(f"AUTHORIZATION FAILED: Validation issues exist: {', '.join(val['blocking_issues'])}")

        current_ver = app.package.versions[0].version if app.package and app.package.versions else 1

        # Revoke any existing active authorizations
        active_auths = db.query(SubmissionAuthorization).filter(
            SubmissionAuthorization.application_id == app.id,
            SubmissionAuthorization.status == "ACTIVE"
        ).all()
        for a in active_auths:
            a.status = "REVOKED"
            a.revoked_at = datetime.now()

        auth = SubmissionAuthorization(
            application_id=app.id,
            package_version=current_ver,
            status="ACTIVE",
            authorized_by=authorized_by,
            expires_at=datetime.now() + timedelta(minutes=duration_minutes)
        )
        db.add(auth)

        app.status = "SUBMISSION_AUTHORIZED"
        db.commit()

        ApplicationAuditService.log_event(db, app.id, "SUBMISSION_AUTHORIZED", authorized_by, {
            "auth_id": auth.id,
            "package_version": current_ver,
            "expires_at": auth.expires_at.strftime("%Y-%m-%d %H:%M:%S")
        })

        db.refresh(auth)
        return auth

    @staticmethod
    def validate_authorization(
        db: Session,
        application_id: int
    ) -> Dict[str, Any]:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return {"valid": False, "reason": "Application not found."}

        auth = (
            db.query(SubmissionAuthorization)
            .filter(SubmissionAuthorization.application_id == app.id)
            .order_by(SubmissionAuthorization.authorized_at.desc())
            .first()
        )
        if not auth:
            return {"valid": False, "reason": "No submission authorization found."}

        # Check status
        if auth.status == "REVOKED":
            return {"valid": False, "reason": "Submission authorization has been REVOKED."}
        if auth.status == "USED":
            return {"valid": False, "reason": "Submission authorization has already been USED."}
        if auth.status != "ACTIVE":
            return {"valid": False, "reason": f"Authorization status is '{auth.status}', expected 'ACTIVE'."}

        # Check expiry
        if datetime.now() > auth.expires_at:
            auth.status = "EXPIRED"
            db.commit()
            return {"valid": False, "reason": "Submission authorization has EXPIRED."}

        # Check package version match
        current_ver = app.package.versions[0].version if app.package and app.package.versions else 1
        if auth.package_version != current_ver:
            return {"valid": False, "reason": f"Package version mismatch: Authorized v{auth.package_version}, current v{current_ver}."}

        # Check application status
        if app.status not in ["APPROVED", "SUBMISSION_AUTHORIZED"]:
            return {"valid": False, "reason": f"Application status is '{app.status}', expected APPROVED or SUBMISSION_AUTHORIZED."}

        return {"valid": True, "authorization": auth}

    @staticmethod
    def revoke_authorization(
        db: Session,
        application_id: int,
        revoked_by: str = "HUMAN_USER"
    ) -> Application:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        auths = db.query(SubmissionAuthorization).filter(
            SubmissionAuthorization.application_id == app.id,
            SubmissionAuthorization.status == "ACTIVE"
        ).all()

        for a in auths:
            a.status = "REVOKED"
            a.revoked_at = datetime.now()

        if app.status == "SUBMISSION_AUTHORIZED":
            app.status = "APPROVED"

        db.commit()
        ApplicationAuditService.log_event(db, app.id, "AUTHORIZATION_REVOKED", revoked_by)
        db.refresh(app)
        return app

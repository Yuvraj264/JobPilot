from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.resume import (
    Resume,
    ResumeSkill,
    ResumeEducation,
    ResumeExperience,
    ResumeProject,
    ResumeCertification,
    ResumeProcessingEvent,
)
from app.services.parser.resume_parser import ResumeParser
from app.services.storage_service import StorageService


class ResumeProcessingService:
    """
    Service executing the complete resume processing pipeline:
    UPLOADED -> PROCESSING -> Extract & Parse -> Persist Structured Entities -> PROCESSED / FAILED
    """

    @staticmethod
    def process_resume(db: Session, resume: Resume) -> Resume:
        # Step 1: Update status to PROCESSING
        resume.processing_status = "PROCESSING"
        resume.processing_error = None
        db.add(ResumeProcessingEvent(
            resume_id=resume.id,
            event_type="PARSE_START",
            message="Started text extraction and section parsing.",
        ))
        db.commit()

        try:
            # Step 2: Resolve absolute storage path
            abs_path = StorageService.resolve_path(resume.file_path)

            # Step 3: Run ResumeParser
            parser = ResumeParser()
            parsed_data = parser.parse_file(abs_path, resume.file_type)

            # Step 4: Clear pre-existing extracted entities for reprocessing
            db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume.id).delete()
            db.query(ResumeEducation).filter(ResumeEducation.resume_id == resume.id).delete()
            db.query(ResumeExperience).filter(ResumeExperience.resume_id == resume.id).delete()
            db.query(ResumeProject).filter(ResumeProject.resume_id == resume.id).delete()
            db.query(ResumeCertification).filter(ResumeCertification.resume_id == resume.id).delete()

            # Step 5: Save Extracted Skills
            for s in parsed_data.get("skills", []):
                db.add(ResumeSkill(
                    resume_id=resume.id,
                    name=s["name"],
                    category=s.get("category", "Other"),
                ))

            # Step 6: Save Extracted Education
            for e in parsed_data.get("education", []):
                db.add(ResumeEducation(
                    resume_id=resume.id,
                    institution=e.get("institution", "Unknown Institution"),
                    degree=e.get("degree", "Qualification"),
                    field_of_study=e.get("field_of_study"),
                    start_year=e.get("start_year"),
                    end_year=e.get("end_year"),
                    grade_or_cgpa=e.get("grade_or_cgpa"),
                ))

            # Step 7: Save Extracted Experience
            for exp in parsed_data.get("experience", []):
                db.add(ResumeExperience(
                    resume_id=resume.id,
                    company=exp.get("company", "Company"),
                    role=exp.get("role", "Role"),
                    location=exp.get("location"),
                    start_date=exp.get("start_date"),
                    end_date=exp.get("end_date"),
                    currently_working=exp.get("currently_working", False),
                    description=exp.get("description"),
                ))

            # Step 8: Save Extracted Projects
            for proj in parsed_data.get("projects", []):
                db.add(ResumeProject(
                    resume_id=resume.id,
                    name=proj.get("name", "Project"),
                    description=proj.get("description"),
                    technologies=proj.get("technologies", []),
                    project_url=proj.get("project_url"),
                    start_date=proj.get("start_date"),
                    end_date=proj.get("end_date"),
                ))

            # Step 9: Save Extracted Certifications
            for cert in parsed_data.get("certifications", []):
                db.add(ResumeCertification(
                    resume_id=resume.id,
                    name=cert.get("name", "Certification"),
                    issuing_organization=cert.get("issuing_organization", "Issuer"),
                    issue_date=cert.get("issue_date"),
                    expiry_date=cert.get("expiry_date"),
                    credential_url=cert.get("credential_url"),
                ))

            # Step 10: Mark as PROCESSED
            resume.processing_status = "PROCESSED"
            db.add(ResumeProcessingEvent(
                resume_id=resume.id,
                event_type="PARSE_SUCCESS",
                message="Text extraction and structured parsing completed successfully.",
            ))
            db.commit()
            db.refresh(resume)
            return resume

        except Exception as e:
            db.rollback()
            resume.processing_status = "FAILED"
            resume.processing_error = str(e)
            db.add(ResumeProcessingEvent(
                resume_id=resume.id,
                event_type="PARSE_ERROR",
                message=f"Parsing failed: {str(e)}",
            ))
            db.commit()
            db.refresh(resume)
            return resume

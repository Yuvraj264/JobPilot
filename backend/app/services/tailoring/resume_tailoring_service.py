import os
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.job import Job
from app.models.tailoring import TailoredResume, ResumeTailoringRun
from app.services.tailoring.requirement_extractor import JobRequirementExtractor
from app.services.tailoring.tailoring_plan import ResumeTailoringPlan
from app.services.tailoring.truthfulness_validator import ResumeTruthfulnessValidator
from app.services.tailoring.change_tracker import ChangeTracker
from app.services.tailoring.keyword_analyzer import ResumeKeywordAnalyzer
from app.services.tailoring.renderers.standard_pdf_renderer import StandardPDFRenderer
from app.services.tailoring.renderers.standard_docx_renderer import StandardDOCXRenderer


class ResumeTailoringService:
    """
    Resume Tailoring Service orchestrating requirement extraction, evidence selection,
    tailoring plan generation, truthfulness validation, change tracking, and PDF/DOCX rendering.
    """

    @staticmethod
    def tailor_resume(
        db: Session,
        profile: UserProfile,
        job: Job,
        master_resume: Optional[Resume] = None
    ) -> TailoredResume:

        # 1. Create Tailoring Run DB Audit Log
        run = ResumeTailoringRun(
            profile_id=profile.id,
            resume_id=master_resume.id if master_resume else None,
            job_id=job.id,
            status="RUNNING"
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # 2. Extract Requirements & Generate Tailoring Plan
        reqs = JobRequirementExtractor.extract_requirements(job)
        plan = ResumeTailoringPlan.generate_plan(job, profile, reqs, master_resume)

        # 3. Construct Intermediate Structured Resume Document
        header = {
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone or "",
            "location": f"{profile.current_city or ''}, {profile.current_country or ''}".strip(", ")
        }

        # Skills reordered by tailoring plan
        skills = [{"name": s_name} for s_name in plan["skills_prioritized"]]

        # Projects ranked by relevance score
        projects = []
        for p in plan["projects_prioritized"]:
            projects.append({
                "name": p["name"],
                "description": p["description"],
                "technologies": p["technologies"],
                "relevance_score": p["relevance_score"]
            })

        # Experience from master resume (preserving factual employers & dates)
        experience = []
        if master_resume and master_resume.experiences:
            for exp in master_resume.experiences:
                experience.append({
                    "company": exp.company_name,
                    "role": exp.role_title,
                    "description": exp.description
                })

        # Education from profile
        education = []
        for ed in (profile.education or []):
            education.append({
                "institution": ed.institution,
                "degree": ed.degree,
                "field_of_study": ed.field_of_study
            })

        # Certifications from profile
        certifications = []
        for cert in (profile.certifications or []):
            certifications.append({
                "name": cert.name,
                "issuing_organization": cert.issuing_organization
            })

        summary = f"Results-driven {profile.current_role or 'Software Professional'} with {profile.years_of_experience or 0.0} years of experience specializing in {', '.join(plan['skills_prioritized'][:3])}. Seeking the {job.title or 'Target Role'} position at {job.company_name or 'Target Company'}."

        doc_dict = {
            "header": header,
            "summary": summary,
            "skills": skills,
            "projects": projects,
            "experience": experience,
            "education": education,
            "certifications": certifications
        }

        # 4. Mandatory Truthfulness Validation
        val_res = ResumeTruthfulnessValidator.validate_tailored_resume(doc_dict, profile, master_resume)
        if not val_res["valid"]:
            run.status = "FAILED"
            run.validation_status = "FAILED_TRUTHFULNESS_CHECK"
            run.error_message = " | ".join(val_res["issues"])
            db.commit()
            raise ValueError(f"Resume Tailoring failed Truthfulness Check: {run.error_message}")

        # 5. Compute Change Tracking & Keyword Analysis
        changes = ChangeTracker.compute_changes(doc_dict, profile, master_resume)
        kw_analysis = ResumeKeywordAnalyzer.analyze_keywords(reqs, profile, master_resume)

        # 6. Render PDF and DOCX documents
        os.makedirs("./storage/tailored_resumes", exist_ok=True)
        pdf_path = f"./storage/tailored_resumes/tailored_{profile.id}_{job.id}.pdf"
        docx_path = f"./storage/tailored_resumes/tailored_{profile.id}_{job.id}.docx"

        StandardPDFRenderer.render_pdf(doc_dict, pdf_path)
        StandardDOCXRenderer.render_docx(doc_dict, docx_path)

        # 7. Create TailoredResume DB Record
        tailored_rec = TailoredResume(
            profile_id=profile.id,
            source_resume_id=master_resume.id if master_resume else None,
            job_id=job.id,
            title=f"Tailored Resume - {job.title} ({job.company_name})",
            status="VALIDATED",
            pdf_file_path=pdf_path,
            docx_file_path=docx_path,
            structured_content=doc_dict,
            change_report=changes,
            keyword_analysis=kw_analysis,
            relevance_score=kw_analysis["coverage_percentage"]
        )
        db.add(tailored_rec)

        # Update Run Record
        run.status = "COMPLETED"
        run.requirements_found = len(reqs)
        run.evidence_items = kw_analysis["matched_count"]
        run.changes_count = changes["total_changes"]
        run.validation_status = "PASSED"
        db.commit()

        db.refresh(tailored_rec)
        return tailored_rec

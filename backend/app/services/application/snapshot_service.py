from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.job import Job
from app.models.matching import JobMatch
from app.models.tailoring import TailoredResume
from app.models.screening import ApplicationQuestion, ApplicationAnswer
from app.models.application import ApplicationSnapshot, Application


class ApplicationSnapshotService:
    """
    Application Snapshot Service capturing immutable historical snapshots of candidate profile,
    resume, tailored content, answers, and job details at application creation/approval time.
    """

    @staticmethod
    def create_snapshot(
        db: Session,
        application_id: int
    ) -> ApplicationSnapshot:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise ValueError(f"Application {application_id} not found.")

        profile = app.profile
        job = app.job
        match = app.match
        tailored = app.tailored_resume
        resume = app.selected_resume

        # 1. Profile Snapshot
        profile_snap = {
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "city": profile.current_city,
            "country": profile.current_country,
            "current_role": profile.current_role,
            "years_of_experience": profile.years_of_experience,
            "skills": [s.name for s in (profile.skills or [])]
        }

        # 2. Job Snapshot
        job_snap = {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name,
            "job_url": job.job_url or job.application_url,
            "location": job.location,
            "employment_type": job.employment_type
        }

        # 3. Match Snapshot
        match_snap = {
            "overall_score": match.overall_score if match else 0.0,
            "component_scores": match.component_scores if match else {}
        }

        # 4. Resume & Tailored Resume Snapshot
        resume_snap = {
            "source_resume_id": resume.id if resume else None,
            "source_filename": resume.original_filename if resume else None,
            "tailored_resume_id": tailored.id if tailored else None,
            "tailored_summary": tailored.structured_content.get("summary") if tailored and tailored.structured_content else None,
            "relevance_score": tailored.relevance_score if tailored else 0.0
        }

        # 5. Answers Snapshot
        answers = []
        if job:
            questions = db.query(ApplicationQuestion).filter(ApplicationQuestion.job_id == job.id).all()
            for q in questions:
                ans = db.query(ApplicationAnswer).filter(ApplicationAnswer.question_id == q.id).first()
                if ans:
                    answers.append({
                        "question_id": q.id,
                        "question_text": q.question_text,
                        "answer_text": ans.answer_text,
                        "answer_source": q.answer_source,
                        "confidence_score": ans.confidence
                    })

        snap = ApplicationSnapshot(
            application_id=app.id,
            profile_snapshot=profile_snap,
            job_snapshot=job_snap,
            match_snapshot=match_snap,
            resume_snapshot=resume_snap,
            answers_snapshot={"answers": answers}
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)
        return snap

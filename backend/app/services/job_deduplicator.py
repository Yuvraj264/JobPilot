from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.job import Job


class JobDeduplicator:
    """
    Deterministic Job Deduplication Service.
    Detects exact duplicate postings (same URL or external ID) and flags cross-source matches as POTENTIAL_DUPLICATE.
    """

    @staticmethod
    def check_duplicate(db: Session, normalized_job: dict, source_id: int) -> Tuple[str, Optional[Job]]:
        """
        Evaluates duplicate status.
        Returns: (status, existing_job)
        Possible statuses: "DUPLICATE", "POTENTIAL_DUPLICATE", "UNIQUE"
        """
        job_url = normalized_job.get("job_url")
        ext_id = normalized_job.get("external_job_id")
        title = normalized_job.get("title")
        company = normalized_job.get("company_name")
        location = normalized_job.get("normalized_location") or normalized_job.get("location")

        # 1. Exact URL Match
        if job_url:
            existing_by_url = db.query(Job).filter(Job.job_url == job_url).first()
            if existing_by_url:
                return "DUPLICATE", existing_by_url

        # 2. Exact Source ID + External Job ID Match
        if ext_id and source_id:
            existing_by_ext = db.query(Job).filter(Job.source_id == source_id, Job.external_job_id == ext_id).first()
            if existing_by_ext:
                return "DUPLICATE", existing_by_ext

        # 3. Cross-Source Potential Duplicate Match (Title + Company + Location)
        if title and company:
            query = db.query(Job).filter(
                Job.title.ilike(title),
                Job.company_name.ilike(company),
            )
            if location:
                query = query.filter(Job.normalized_location.ilike(location))

            existing_cross_source = query.first()
            if existing_cross_source:
                return "POTENTIAL_DUPLICATE", existing_cross_source

        return "UNIQUE", None

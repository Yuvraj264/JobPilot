import re
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.job import Job


class JobDeduplicator:
    """
    Deterministic Job Deduplication Service.
    Detects exact duplicate postings (same URL or external ID) and flags cross-source matches as POTENTIAL_DUPLICATE.
    """

    @staticmethod
    def jaccard_similarity(str1: str, str2: str) -> float:
        if not str1 or not str2:
            return 0.0
        words1 = set(re.findall(r'\w+', str1.lower()))
        words2 = set(re.findall(r'\w+', str2.lower()))
        if not words1 or not words2:
            return 0.0
        return len(words1.intersection(words2)) / len(words1.union(words2))

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
        desc = normalized_job.get("description") or ""

        # 1. Exact URL Match
        if job_url:
            existing_by_url = db.query(Job).filter(Job.job_url == job_url).first()
            if existing_by_url:
                # Same URL from same source = DUPLICATE. Different source = POTENTIAL_DUPLICATE.
                if existing_by_url.source_id == source_id:
                    return "DUPLICATE", existing_by_url
                else:
                    return "POTENTIAL_DUPLICATE", existing_by_url

        # 2. Exact Source ID + External Job ID Match
        if ext_id and source_id:
            existing_by_ext = db.query(Job).filter(Job.source_id == source_id, Job.external_job_id == ext_id).first()
            if existing_by_ext:
                return "DUPLICATE", existing_by_ext

        # 3. Cross-Source External Job ID Match
        if ext_id:
            existing_cross_ext = db.query(Job).filter(Job.external_job_id == ext_id, Job.source_id != source_id).first()
            if existing_cross_ext:
                return "POTENTIAL_DUPLICATE", existing_cross_ext

        # 4. Cross-Source Match (Title + Company + Location + Description Similarity)
        if title and company:
            # Query jobs with similar title and company
            similar_jobs = db.query(Job).filter(
                Job.title.ilike(f"%{title}%"),
                Job.company_name.ilike(f"%{company}%")
            ).all()

            for existing in similar_jobs:
                # Check location mismatch
                loc_match = True
                if location and existing.normalized_location:
                    # If locations are provided and completely different, it might not be a duplicate
                    if location.lower() not in existing.normalized_location.lower() and existing.normalized_location.lower() not in location.lower():
                        loc_match = False

                if loc_match:
                    # Check description similarity if practical
                    desc_sim = JobDeduplicator.jaccard_similarity(desc, existing.description or "")
                    if desc_sim >= 0.65 or not desc or not existing.description:
                        return "POTENTIAL_DUPLICATE", existing

        return "UNIQUE", None

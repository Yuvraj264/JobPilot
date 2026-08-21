import pytest
from app.database.connection import SessionLocal
from app.models.job import Job, JobSource
from app.services.job_deduplicator import JobDeduplicator


def test_job_deduplication():
    db = SessionLocal()
    try:
        source = db.query(JobSource).filter(JobSource.name == "dedup_src").first()
        if not source:
            source = JobSource(name="dedup_src", display_name="Dedup Source", source_type="WEB")
            db.add(source)
            db.commit()
            db.refresh(source)

        existing_job = Job(
            source_id=source.id,
            external_job_id="EXT-100",
            title="QA Automation Engineer",
            company_name="Acme QA",
            job_url="https://acmeqa.example.com/job/100",
            location="Bengaluru, India",
            normalized_location="Bengaluru, India",
            status="ACTIVE",
        )
        db.add(existing_job)
        db.commit()

        # 1. Exact URL Match
        dup_status, dup_job = JobDeduplicator.check_duplicate(
            db, {"job_url": "https://acmeqa.example.com/job/100"}, source_id=source.id
        )
        assert dup_status == "DUPLICATE"
        assert dup_job.id == existing_job.id

        # 2. Exact Source ID + External ID Match
        dup_status_ext, _ = JobDeduplicator.check_duplicate(
            db, {"external_job_id": "EXT-100"}, source_id=source.id
        )
        assert dup_status_ext == "DUPLICATE"

        # 3. Cross-Source Potential Match
        dup_status_cross, _ = JobDeduplicator.check_duplicate(
            db,
            {
                "title": "QA Automation Engineer",
                "company_name": "Acme QA",
                "normalized_location": "Bengaluru, India",
            },
            source_id=99,
        )
        assert dup_status_cross == "POTENTIAL_DUPLICATE"

    finally:
        db.close()

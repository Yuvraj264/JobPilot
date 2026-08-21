from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.job import JobSource, RawJob, Job, JobDiscoveryRun
from app.services.adapters.base import JobSourceAdapter
from app.services.adapters.registry import registry
from app.services.normalization.job_normalizer import JobNormalizer
from app.services.job_deduplicator import JobDeduplicator


class JobDiscoveryService:
    """
    Discovery Engine executing end-to-end job ingestion:
    Adapter -> RawJob -> Normalizer -> Deduplicator -> PostgreSQL -> JobDiscoveryRun Summary
    """

    @staticmethod
    def sync_job_source_record(db: Session, adapter: JobSourceAdapter) -> JobSource:
        """
        Ensures JobSource database record exists for target adapter.
        """
        source = db.query(JobSource).filter(JobSource.name == adapter.source_name()).first()
        if not source:
            source = JobSource(
                name=adapter.source_name(),
                display_name=adapter.display_name(),
                source_type=adapter.source_type(),
                enabled=registry.is_enabled(adapter.source_name()),
            )
            db.add(source)
            db.commit()
            db.refresh(source)
        return source

    @staticmethod
    def run_discovery_for_source(db: Session, adapter: JobSourceAdapter, limit: int = 50, page: int = 1) -> Dict[str, Any]:
        """
        Executes discovery pipeline for a single source adapter.
        Partial malformed job errors do NOT halt the discovery run.
        """
        source_rec = JobDiscoveryService.sync_job_source_record(db, adapter)
        
        # Start Discovery Run Audit Log
        discovery_run = JobDiscoveryRun(
            source_id=source_rec.id,
            started_at=datetime.now(timezone.utc),
            status="RUNNING",
        )
        db.add(discovery_run)
        db.commit()
        db.refresh(discovery_run)

        count_discovered = 0
        count_created = 0
        count_updated = 0
        count_duplicates = 0
        count_invalid = 0

        try:
            raw_items = adapter.discover_jobs(limit=limit, page=page)
            count_discovered = len(raw_items)

            for item in raw_items:
                # Step 1: Save Raw Job
                raw_job = RawJob(
                    source_id=source_rec.id,
                    external_job_id=item.get("external_id") or item.get("external_job_id"),
                    raw_title=item.get("title") or item.get("raw_title"),
                    raw_company=item.get("company") or item.get("raw_company"),
                    raw_location=item.get("location") or item.get("raw_location"),
                    raw_description=item.get("description") or item.get("raw_description"),
                    raw_url=item.get("job_url") or item.get("raw_url"),
                    raw_payload=item,
                )
                db.add(raw_job)
                db.commit()
                db.refresh(raw_job)

                # Step 2: Normalize
                try:
                    norm_dict = JobNormalizer.normalize_raw_job(item)
                except ValueError as val_err:
                    count_invalid += 1
                    continue  # Log invalid job and continue processing remaining items

                # Step 3: Deduplicate
                dup_status, existing_job = JobDeduplicator.check_duplicate(db, norm_dict, source_rec.id)

                if dup_status == "DUPLICATE":
                    count_duplicates += 1
                    if existing_job:
                        existing_job.updated_at = datetime.now(timezone.utc)
                        db.commit()
                        count_updated += 1
                    continue

                # Step 4: Persist Normalized Job
                final_status = "POTENTIAL_DUPLICATE" if dup_status == "POTENTIAL_DUPLICATE" else "DISCOVERED"
                if dup_status == "POTENTIAL_DUPLICATE":
                    count_duplicates += 1

                new_job = Job(
                    raw_job_id=raw_job.id,
                    source_id=source_rec.id,
                    external_job_id=norm_dict["external_job_id"],
                    title=norm_dict["title"],
                    company_name=norm_dict["company_name"],
                    company_url=norm_dict["company_url"],
                    job_url=norm_dict["job_url"],
                    location=norm_dict["location"],
                    normalized_location=norm_dict["normalized_location"],
                    description=norm_dict["description"],
                    employment_type=norm_dict["employment_type"],
                    workplace_type=norm_dict["workplace_type"],
                    experience_min=norm_dict["experience_min"],
                    experience_max=norm_dict["experience_max"],
                    salary_min=norm_dict["salary_min"],
                    salary_max=norm_dict["salary_max"],
                    salary_currency=norm_dict["salary_currency"],
                    posted_at=norm_dict["posted_at"],
                    application_url=norm_dict["application_url"],
                    source_metadata=norm_dict["source_metadata"],
                    status=final_status,
                )
                db.add(new_job)
                db.commit()
                count_created += 1

            # Update Source & Discovery Run Status
            source_rec.last_successful_run = datetime.now(timezone.utc)
            source_rec.last_error = None
            db.commit()

            discovery_run.status = "COMPLETED" if count_invalid == 0 else "PARTIAL"
            discovery_run.completed_at = datetime.now(timezone.utc)
            discovery_run.jobs_discovered = count_discovered
            discovery_run.jobs_created = count_created
            discovery_run.jobs_updated = count_updated
            discovery_run.duplicates = count_duplicates
            discovery_run.invalid_jobs = count_invalid
            db.commit()

            return {
                "source": adapter.source_name(),
                "status": discovery_run.status,
                "jobs_discovered": count_discovered,
                "jobs_created": count_created,
                "jobs_updated": count_updated,
                "duplicates": count_duplicates,
                "invalid_jobs": count_invalid,
            }

        except Exception as run_err:
            db.rollback()
            source_rec.last_failed_run = datetime.now(timezone.utc)
            source_rec.last_error = str(run_err)
            db.commit()

            discovery_run.status = "FAILED"
            discovery_run.completed_at = datetime.now(timezone.utc)
            discovery_run.error_message = str(run_err)
            db.commit()
            raise run_err

    @staticmethod
    def run_discovery_all_enabled(db: Session, limit_per_source: int = 50) -> List[Dict[str, Any]]:
        results = []
        enabled_adapters = registry.get_enabled_adapters()
        for adapter in enabled_adapters:
            try:
                res = JobDiscoveryService.run_discovery_for_source(db, adapter, limit=limit_per_source)
                results.append(res)
            except Exception as e:
                results.append({
                    "source": adapter.source_name(),
                    "status": "FAILED",
                    "error": str(e),
                })
        return results

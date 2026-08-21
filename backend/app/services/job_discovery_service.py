import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.job import JobSource, RawJob, Job, JobDiscoveryRun, SourceConfiguration
from app.services.adapters.base import JobSourceAdapter, AdapterError, RateLimitedError, AuthenticationRequiredError
from app.services.adapters.registry import registry
from app.services.normalization.job_normalizer import JobNormalizer
from app.services.job_deduplicator import JobDeduplicator

logger = logging.getLogger(__name__)


class JobDiscoveryService:
    """
    Discovery Engine executing end-to-end job ingestion:
    Adapter -> RawJob -> Normalizer -> Deduplicator -> PostgreSQL -> JobDiscoveryRun Summary
    Also handles Job Freshness (ACTIVE/STALE/EXPIRED) and URL Verification.
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
        
        # Ensure SourceConfiguration record exists
        JobDiscoveryService.get_or_create_source_config(db, source)
        return source

    @staticmethod
    def get_or_create_source_config(db: Session, source: JobSource) -> SourceConfiguration:
        """
        Retrieves or creates default SourceConfiguration for a JobSource.
        """
        config = db.query(SourceConfiguration).filter(SourceConfiguration.source_id == source.id).first()
        if not config:
            # Default configuration structure
            default_config = {}
            if source.name == "company_careers":
                # Create pre-configured entries for synthetic sites A, B, and C
                default_config = {
                    "company_name": "Synthetic Site Hub",
                    "careers_url": "http://localhost:8000/mock/synthetic-careers/site_a",
                    "discovery_method": "DOM_SELECTORS",
                    "parser_configuration": {
                        "job_card_selector": ".job-card",
                        "job_link_selector": "a.job-link",
                        "job_title_selector": ".job-title",
                        "company_selector": ".job-company",
                        "location_selector": ".job-location",
                        "description_selector": ".job-description",
                        "salary_selector": ".job-salary",
                        "experience_selector": ".job-experience",
                        "next_page_selector": "a.next-page",
                        "delay_between_requests": 0.5
                    }
                }
            config = SourceConfiguration(
                source_id=source.id,
                enabled=source.enabled,
                discovery_enabled=True,
                application_enabled=False,
                max_jobs_per_run=50,
                max_pages_per_run=5,
                rate_limit=60.0,
                configuration=default_config
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        return config

    @staticmethod
    def run_discovery_for_source(db: Session, adapter: JobSourceAdapter, limit: int = 50, page: int = 1) -> Dict[str, Any]:
        """
        Executes discovery pipeline for a single source adapter.
        Partial malformed job errors do NOT halt the discovery run.
        """
        source_rec = JobDiscoveryService.sync_job_source_record(db, adapter)
        config_rec = JobDiscoveryService.get_or_create_source_config(db, source_rec)

        if not config_rec.enabled or not config_rec.discovery_enabled:
            return {
                "source": adapter.source_name(),
                "status": "SKIPPED",
                "notes": "Source discovery is disabled in configuration."
            }

        # Initialize tracking metrics on the adapter instance
        adapter.pages_visited = 0
        adapter.requests_made = 0
        adapter.rate_limit_events = 0
        adapter.authentication_events = 0
        
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
        active_external_ids = []

        try:
            # Respect configured limits if they override default
            run_limit = config_rec.max_jobs_per_run or limit
            
            raw_items = adapter.discover_jobs(limit=run_limit, page=page)
            count_discovered = len(raw_items)

            for item in raw_items:
                ext_id = item.get("external_id") or item.get("external_job_id")
                if ext_id:
                    active_external_ids.append(str(ext_id))

                # Step 1: Save Raw Job
                raw_job = RawJob(
                    source_id=source_rec.id,
                    external_job_id=ext_id,
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
                    continue  # Log invalid job and continue

                # Step 3: Deduplicate
                dup_status, existing_job = JobDeduplicator.check_duplicate(db, norm_dict, source_rec.id)

                if dup_status == "DUPLICATE":
                    count_duplicates += 1
                    if existing_job:
                        existing_job.last_seen_at = datetime.now(timezone.utc)
                        existing_job.updated_at = datetime.now(timezone.utc)
                        # Keep status ACTIVE if it was active
                        if existing_job.status in ["STALE", "UNKNOWN"]:
                            existing_job.status = "ACTIVE"
                        db.commit()
                        count_updated += 1
                    continue

                # Step 4: Persist Normalized Job
                final_status = "POTENTIAL_DUPLICATE" if dup_status == "POTENTIAL_DUPLICATE" else "ACTIVE"
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
                    last_seen_at=datetime.now(timezone.utc),
                )
                db.add(new_job)
                db.commit()
                count_created += 1

            # Step 5: Refresh job freshness
            stale_count = 0
            if active_external_ids:
                stale_count = JobDiscoveryService.refresh_job_freshness(db, source_rec.id, active_external_ids)

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
            
            # Save enhanced metrics
            discovery_run.pages_visited = getattr(adapter, "pages_visited", 0)
            discovery_run.requests_made = getattr(adapter, "requests_made", 0)
            discovery_run.rate_limit_events = getattr(adapter, "rate_limit_events", 0)
            discovery_run.authentication_events = getattr(adapter, "authentication_events", 0)
            discovery_run.source_status = "healthy"
            discovery_run.stale_jobs = stale_count
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
            
            # Map exception types to run status
            status_str = "error"
            if isinstance(run_err, RateLimitedError):
                status_str = "rate_limited"
                discovery_run.rate_limit_events += 1
            elif isinstance(run_err, AuthenticationRequiredError):
                status_str = "authentication_required"
                discovery_run.authentication_events += 1
            
            discovery_run.source_status = status_str
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

    # --- JOB FRESHNESS ---
    @staticmethod
    def refresh_job_freshness(db: Session, source_id: int, active_external_ids: List[str], stale_days: int = 7, expire_days: int = 14) -> int:
        """
        Updates the status of jobs from a source depending on when they were last seen in discovery.
        States: ACTIVE, STALE, EXPIRED, UNKNOWN.
        """
        now = datetime.now(timezone.utc)
        
        # 1. Update jobs seen in this run to ACTIVE (or keep as DISCOVERED / POTENTIAL_DUPLICATE)
        db.query(Job).filter(
            Job.source_id == source_id,
            Job.external_job_id.in_(active_external_ids)
        ).update(
            {Job.last_seen_at: now},
            synchronize_session=False
        )
        db.commit()

        # 2. Identify jobs from this source not seen in this run
        stale_threshold = now - timedelta(days=stale_days)
        expire_threshold = now - timedelta(days=expire_days)

        # Transition to EXPIRED
        expired_count = db.query(Job).filter(
            Job.source_id == source_id,
            ~Job.external_job_id.in_(active_external_ids),
            Job.last_seen_at < expire_threshold,
            Job.status != "EXPIRED"
        ).update(
            {Job.status: "EXPIRED"},
            synchronize_session=False
        )

        # Transition to STALE
        stale_count = db.query(Job).filter(
            Job.source_id == source_id,
            ~Job.external_job_id.in_(active_external_ids),
            Job.last_seen_at < stale_threshold,
            Job.last_seen_at >= expire_threshold,
            Job.status != "STALE"
        ).update(
            {Job.status: "STALE"},
            synchronize_session=False
        )

        db.commit()
        return stale_count + expired_count

    # --- JOB URL VERIFICATION ---
    @staticmethod
    def verify_job_urls(db: Session, age_hours: int = 24, max_jobs_to_verify: int = 15) -> Dict[str, Any]:
        """
        Verifies that stored job URLs are still reachable without hammering.
        States: REACHABLE, NOT_FOUND, REDIRECTED, BLOCKED, UNKNOWN
        """
        threshold = datetime.now(timezone.utc) - timedelta(hours=age_hours)
        jobs_to_verify = db.query(Job).filter(
            Job.job_url != None,
            or_(
                Job.url_verified_at == None,
                Job.url_verified_at < threshold
            )
        ).limit(max_jobs_to_verify).all()

        results = {
            "verified": 0,
            "reachable": 0,
            "not_found": 0,
            "redirected": 0,
            "blocked": 0,
            "unknown": 0
        }

        if not jobs_to_verify:
            return results

        # Standard headers to look like a friendly browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        with httpx.Client(timeout=3.0, headers=headers, follow_redirects=False) as client:
            for job in jobs_to_verify:
                status = "UNKNOWN"
                try:
                    res = client.get(job.job_url)
                    if res.status_code >= 200 and res.status_code < 300:
                        status = "REACHABLE"
                        results["reachable"] += 1
                    elif res.status_code >= 300 and res.status_code < 400:
                        status = "REDIRECTED"
                        results["redirected"] += 1
                    elif res.status_code == 404:
                        status = "NOT_FOUND"
                        results["not_found"] += 1
                    elif res.status_code in [401, 403]:
                        status = "BLOCKED"
                        results["blocked"] += 1
                    else:
                        status = "UNKNOWN"
                        results["unknown"] += 1
                except httpx.HTTPError:
                    status = "UNKNOWN"
                    results["unknown"] += 1
                
                job.url_status = status
                job.url_verified_at = datetime.now(timezone.utc)
                results["verified"] += 1
            
            db.commit()

        return results

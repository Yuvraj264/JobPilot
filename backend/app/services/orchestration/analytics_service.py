from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.job import Job, JobSource
from app.models.matching import JobMatch
from app.models.application import Application, SubmissionRun, HumanInterventionEvent
from app.models.orchestration import OrchestrationRun, DailyAutomationMetric, AutomationConfiguration
from app.models.profile import Skill

class AnalyticsService:
    """
    Computes analytical funnel matrices, failure groupings, and match score distributions.
    """

    @classmethod
    def get_overview_metrics(cls, db: Session, profile_id: int) -> Dict[str, Any]:
        """
        Gathers general dashboard count indicators and application conversion percentages.
        """
        # Daily metric aggregation
        today = datetime.now().date()
        today_metrics = db.query(DailyAutomationMetric).filter(
            DailyAutomationMetric.profile_id == profile_id,
            DailyAutomationMetric.date == today
        ).first()

        # Funnel stage counts
        total_discovered = db.query(Job).count()
        total_eligible = db.query(JobMatch).filter(JobMatch.profile_id == profile_id, JobMatch.overall_score >= 70).count()
        total_high_match = db.query(JobMatch).filter(JobMatch.profile_id == profile_id, JobMatch.overall_score >= 80).count()
        total_prepared = db.query(Application).filter(Application.profile_id == profile_id).count()
        total_approved = db.query(Application).filter(Application.profile_id == profile_id, Application.status.in_(["APPROVED", "SUBMISSION_AUTHORIZED", "SUBMITTED"])).count()
        total_submitted = db.query(Application).filter(Application.profile_id == profile_id, Application.status == "SUBMITTED").count()
        total_verified = total_submitted  # verified is matching submitted confirmation

        return {
            "today": {
                "discovered": today_metrics.jobs_discovered if today_metrics else 0,
                "matched": today_metrics.jobs_matched if today_metrics else 0,
                "prepared": today_metrics.applications_prepared if today_metrics else 0,
                "submitted": today_metrics.applications_submitted if today_metrics else 0,
                "failed": today_metrics.applications_failed if today_metrics else 0,
                "average_match_score": today_metrics.average_match_score if today_metrics else 0.0
            },
            "funnel": {
                "discovered": total_discovered,
                "eligible": total_eligible,
                "high_match": total_high_match,
                "prepared": total_prepared,
                "approved": total_approved,
                "submitted": total_submitted,
                "verified": total_verified
            }
        }

    @classmethod
    def get_applications_analytics(cls, db: Session, profile_id: int) -> Dict[str, Any]:
        """
        Gathers metrics on application submission outcomes and source distribution.
        """
        total = db.query(Application).filter(Application.profile_id == profile_id).count()
        submitted = db.query(Application).filter(Application.profile_id == profile_id, Application.status == "SUBMITTED").count()
        failed = db.query(Application).filter(Application.profile_id == profile_id, Application.status == "FAILED").count()
        paused = db.query(Application).filter(Application.profile_id == profile_id, Application.status == "PAUSED").count()

        # Source distribution
        source_counts = db.query(
            Application.source, func.count(Application.id)
        ).filter(
            Application.profile_id == profile_id
        ).group_by(Application.source).all()

        source_dist = {str(src or "unknown").lower(): count for src, count in source_counts}

        return {
            "total_applications": total,
            "submitted": submitted,
            "failed": failed,
            "paused": paused,
            "success_rate": (submitted / total * 100.0) if total > 0 else 0.0,
            "failure_rate": (failed / total * 100.0) if total > 0 else 0.0,
            "source_distribution": source_dist
        }

    @classmethod
    def get_jobs_analytics(cls, db: Session) -> Dict[str, Any]:
        """
        Summarizes job role, location, and workplace distributions.
        """
        source_counts = db.query(Job.source_id, func.count(Job.id)).group_by(Job.source_id).all()
        
        # Map source IDs to names
        sources_rec = db.query(JobSource).all()
        source_map = {src.id: src.name for src in sources_rec}
        source_dist = {source_map.get(sid, f"source_{sid}"): count for sid, count in source_counts}

        # Workplace types
        workplace_counts = db.query(Job.workplace_type, func.count(Job.id)).group_by(Job.workplace_type).all()
        workplace_dist = {str(wt): count for wt, count in workplace_counts}

        # Locations
        loc_counts = db.query(Job.location, func.count(Job.id)).group_by(Job.location).limit(5).all()
        loc_dist = {str(loc or "unknown"): count for loc, count in loc_counts}

        return {
            "jobs_by_source": source_dist,
            "jobs_by_workplace": workplace_dist,
            "top_locations": loc_dist
        }

    @classmethod
    def get_matching_analytics(cls, db: Session, profile_id: int) -> Dict[str, Any]:
        """
        Gathers match score distribution and top/missing profile skills.
        """
        # Match score intervals
        matches = db.query(JobMatch).filter(JobMatch.profile_id == profile_id).all()
        
        intervals = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "<60": 0
        }

        for m in matches:
            score = m.overall_score or 0.0
            if score >= 90:
                intervals["90-100"] += 1
            elif score >= 80:
                intervals["80-89"] += 1
            elif score >= 70:
                intervals["70-79"] += 1
            elif score >= 60:
                intervals["60-69"] += 1
            else:
                intervals["<60"] += 1

        # Profile skills match summary
        profile_skills = [s.name.lower() for s in db.query(Skill).filter(Skill.profile_id == profile_id).all()]
        
        # Hardcoded common missing tech skills as fallback indicator for analytics views
        common_missing = ["docker", "kubernetes", "aws", "typescript", "react"]
        missing_skills = [s for s in common_missing if s not in profile_skills]

        return {
            "score_distribution": intervals,
            "matching_skills_count": len(profile_skills),
            "common_missing_skills": missing_skills[:5]
        }

    @classmethod
    def get_failures_analytics(cls, db: Session, profile_id: int) -> Dict[str, Any]:
        """
        Groups run failures by cause categories.
        """
        runs = db.query(SubmissionRun).join(Application).filter(
            Application.profile_id == profile_id,
            SubmissionRun.status == "FAILED"
        ).all()

        categories = {
            "missing_data": 0,
            "validation": 0,
            "browser": 0,
            "source": 0,
            "authentication": 0,
            "captcha": 0,
            "timeout": 0,
            "duplicate": 0,
            "authorization": 0,
            "other": 0
        }

        for r in runs:
            err = str(r.error_message or "").lower()
            if "captcha" in err:
                categories["captcha"] += 1
            elif "authorization" in err or "expired token" in err:
                categories["authorization"] += 1
            elif "validation" in err:
                categories["validation"] += 1
            elif "timeout" in err:
                categories["timeout"] += 1
            elif "network" in err or "connection" in err:
                categories["browser"] += 1
            elif "duplicate" in err:
                categories["duplicate"] += 1
            elif "login" in err or "credentials" in err:
                categories["authentication"] += 1
            elif "missing field" in err or "profile info" in err:
                categories["missing_data"] += 1
            elif "source" in err or "disabled" in err:
                categories["source"] += 1
            else:
                categories["other"] += 1

        return categories

    @classmethod
    def get_sources_analytics(cls, db: Session, profile_id: int) -> List[Dict[str, Any]]:
        """
        Calculates application success and failure rate statistics per source target.
        """
        source_data = db.query(
            Application.source,
            func.count(Application.id),
            func.sum(func.case((Application.status == "SUBMITTED", 1), else_=0)),
            func.sum(func.case((Application.status == "FAILED", 1), else_=0))
        ).filter(
            Application.profile_id == profile_id
        ).group_by(Application.source).all()

        results = []
        for src, total, submitted, failed in source_data:
            results.append({
                "source": src or "unknown",
                "total_applications": total,
                "submitted": int(submitted or 0),
                "failed": int(failed or 0),
                "success_rate": (int(submitted or 0) / total * 100.0) if total > 0 else 0.0
            })
        return results

    @classmethod
    def record_daily_metric(
        cls,
        db: Session,
        profile_id: int,
        discovered: int = 0,
        matched: int = 0,
        prepared: int = 0,
        submitted: int = 0,
        failed: int = 0,
        match_score: float = 0.0
    ):
        """
        Upserts daily aggregation analytics metric records.
        """
        today = datetime.now().date()
        metric = db.query(DailyAutomationMetric).filter(
            DailyAutomationMetric.profile_id == profile_id,
            DailyAutomationMetric.date == today
        ).first()

        if not metric:
            metric = DailyAutomationMetric(
                profile_id=profile_id,
                date=today,
                jobs_discovered=discovered,
                jobs_matched=matched,
                applications_prepared=prepared,
                applications_submitted=submitted,
                applications_failed=failed,
                average_match_score=match_score
            )
            db.add(metric)
        else:
            metric.jobs_discovered += discovered
            metric.jobs_matched += matched
            metric.applications_prepared += prepared
            metric.applications_submitted += submitted
            metric.applications_failed += failed
            if match_score > 0.0:
                metric.average_match_score = (metric.average_match_score + match_score) / 2.0

        db.commit()

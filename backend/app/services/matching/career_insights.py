from collections import Counter
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.profile import UserProfile
from app.models.matching import JobMatch
from app.services.matching.skill_matcher import SkillMatcher

class CareerInsights:
    """
    Analyzes aggregated statistics from discovered job listings.
    Helps users identify demand patterns and high-opportunity areas.
    """

    @staticmethod
    def get_insights(db: Session, profile: UserProfile) -> Dict[str, Any]:
        # Fetch all discovered jobs
        jobs = db.query(Job).all()
        total_jobs = len(jobs)
        if total_jobs == 0:
            return {
                "sample_size": 0,
                "most_requested_skills": [],
                "common_missing_skills": [],
                "highest_matching_roles": [],
                "highest_opportunity_locations": [],
                "frequent_technologies": [],
            }

        # User profile skills (normalized)
        user_skills_set = {
            SkillMatcher.normalize_skill_name(s.name).lower()
            for s in (profile.skills or [])
        }

        all_req_skills = []
        missing_skills_counter = Counter()
        tech_counter = Counter()
        location_counter = Counter()
        role_counter = Counter()

        for j in jobs:
            skills = SkillMatcher.extract_job_skills(j)
            req_skills = skills.get("required", [])
            pref_skills = skills.get("preferred", [])
            
            all_req_skills.extend(req_skills)
            
            for s in req_skills:
                if s.lower() not in user_skills_set:
                    missing_skills_counter[s] += 1
            
            # Count locations
            loc = j.normalized_location or j.location
            if loc:
                location_counter[loc] += 1
                
            # Count job titles (roles)
            if j.title:
                role_counter[j.title] += 1

        # Most requested skills (top 10)
        req_skills_counter = Counter(all_req_skills)
        most_requested_skills = [
            {"skill": k, "count": v, "percentage": round((v / total_jobs) * 100, 1)}
            for k, v in req_skills_counter.most_common(10)
        ]

        # Common missing skills (top 10)
        common_missing_skills = [
            {"skill": k, "count": v, "percentage": round((v / total_jobs) * 100, 1)}
            for k, v in missing_skills_counter.most_common(10)
        ]

        # Opportunity locations (top 5)
        highest_opportunity_locations = [
            {"location": k, "count": v}
            for k, v in location_counter.most_common(5)
        ]

        # Highest matching roles (highest average overall scores)
        # Group JobMatches by job title
        matches = db.query(JobMatch).join(Job).filter(JobMatch.profile_id == profile.id).all()
        role_match_scores = {}
        for m in matches:
            t = m.job.title
            if t not in role_match_scores:
                role_match_scores[t] = []
            role_match_scores[t].append(m.overall_score)

        avg_role_matches = []
        for r, scores in role_match_scores.items():
            avg_score = sum(scores) / len(scores)
            avg_role_matches.append({"role": r, "average_score": round(avg_score, 1), "count": len(scores)})
        
        # Sort roles by score descending
        avg_role_matches.sort(key=lambda x: x["average_score"], reverse=True)

        return {
            "sample_size": total_jobs,
            "most_requested_skills": most_requested_skills,
            "common_missing_skills": common_missing_skills,
            "highest_matching_roles": avg_role_matches[:5],
            "highest_opportunity_locations": highest_opportunity_locations,
            "frequent_technologies": [{"name": k, "count": v} for k, v in req_skills_counter.most_common(5)],
        }

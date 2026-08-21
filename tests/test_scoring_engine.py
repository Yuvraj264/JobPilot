import pytest
from app.models.profile import UserProfile, JobPreference, Skill
from app.models.job import Job
from app.models.matching import MatchConfig
from app.services.matching.scoring_engine import ScoringEngine


def test_scoring_engine_recommendations():
    profile = UserProfile(years_of_experience=2.0)
    profile.job_preference = JobPreference(
        target_roles=["QA Automation Engineer"],
        preferred_locations=["Bangalore"],
        work_arrangements=["HYBRID", "REMOTE"]
    )
    profile.skills = [
        Skill(name="Selenium"),
        Skill(name="Python"),
        Skill(name="SQL")
    ]

    config = MatchConfig(
        threshold_apply=80.0,
        threshold_review=65.0
    )

    # 1. High suitability -> APPLY
    job_apply = Job(
        title="QA Automation Engineer",
        company_name="TechCorp",
        location="Bengaluru, India",
        workplace_type="HYBRID",
        employment_type="FULL_TIME",
        description="Required skills: Selenium, Python, SQL."
    )
    res_apply = ScoringEngine.evaluate_job(profile, job_apply, config)
    assert res_apply["eligible"] is True
    assert res_apply["recommendation"] == "APPLY"
    assert res_apply["overall_score"] >= 80.0

    # 2. Hard failure -> SKIP
    job_skip = Job(
        title="Senior Director of QA",
        company_name="BigCorp",
        location="Delhi, India",
        workplace_type="ONSITE",
        experience_min=10.0,
        description="Minimum 10 years experience required."
    )
    res_skip = ScoringEngine.evaluate_job(profile, job_skip, config)
    assert res_skip["eligible"] is False
    assert res_skip["recommendation"] == "SKIP"

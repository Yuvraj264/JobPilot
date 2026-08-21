import pytest
from app.models.profile import UserProfile, JobPreference
from app.models.job import Job
from app.services.matching.role_matcher import RoleMatcher


def test_role_matcher_exact_and_family():
    profile = UserProfile(current_role="QA Engineer")
    profile.job_preference = JobPreference(target_roles=["QA Engineer"])

    # 1. Exact Match
    job_exact = Job(title="QA Engineer")
    res_exact = RoleMatcher.evaluate(profile, job_exact)
    assert res_exact["score"] == 100.0
    assert res_exact["role_match_type"] == "EXACT"

    # 2. Taxonomy Role Family Match ("Software Test Engineer" ~ "QA Engineer")
    job_family = Job(title="Software Test Engineer")
    res_family = RoleMatcher.evaluate(profile, job_family)
    assert res_family["score"] >= 80.0
    assert res_family["role_match_type"] in ["ROLE_FAMILY", "SUBSTRING"]

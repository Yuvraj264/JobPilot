import pytest
from app.models.profile import UserProfile, JobPreference
from app.models.job import Job
from app.services.matching.location_matcher import LocationMatcher


def test_location_matcher_city_equivalence_and_remote():
    profile = UserProfile(current_city="Bangalore")
    profile.job_preference = JobPreference(
        preferred_locations=["Bangalore"],
        work_arrangements=["REMOTE", "HYBRID"]
    )

    # 1. City Equivalence (Bangalore == Bengaluru)
    job_city = Job(title="QA Engineer", location="Bengaluru, India", workplace_type="ONSITE")
    res_city = LocationMatcher.evaluate(profile, job_city)
    assert res_city["score"] == 100.0

    # 2. Remote Job Match
    job_remote = Job(title="QA Engineer", location="Remote", workplace_type="REMOTE")
    res_remote = LocationMatcher.evaluate(profile, job_remote)
    assert res_remote["score"] == 100.0

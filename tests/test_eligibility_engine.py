import pytest
from app.models.profile import UserProfile, JobPreference
from app.models.job import Job
from app.services.matching.eligibility_engine import EligibilityEngine


def test_eligibility_experience_hard_failure():
    profile = UserProfile(years_of_experience=0.0)
    job = Job(title="Senior QA Engineer", description="Minimum 5 years required", experience_min=5.0)

    res = EligibilityEngine.evaluate(profile, job)
    assert res["eligible"] is False
    assert len(res["hard_failures"]) == 1
    assert "Experience Mismatch" in res["hard_failures"][0]


def test_eligibility_fresher_friendly_pass():
    profile = UserProfile(years_of_experience=0.0)
    job = Job(title="Junior QA Tester", description="Freshers welcome! Entry level role.", experience_min=0.0)

    res = EligibilityEngine.evaluate(profile, job)
    assert res["eligible"] is True
    assert len(res["hard_failures"]) == 0


def test_eligibility_location_hard_failure():
    profile = UserProfile(years_of_experience=2.0)
    profile.job_preference = JobPreference(
        preferred_locations=["Bangalore"],
        relocation_status=False
    )
    job = Job(title="QA Engineer", location="Delhi, India", workplace_type="ONSITE")

    res = EligibilityEngine.evaluate(profile, job)
    assert res["eligible"] is False
    assert "Location Constraint" in res["hard_failures"][0]

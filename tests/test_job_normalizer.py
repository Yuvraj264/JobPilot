import pytest
from app.services.normalization.location_normalizer import LocationNormalizer
from app.services.normalization.employment_type_normalizer import EmploymentTypeNormalizer
from app.services.normalization.workplace_type_normalizer import WorkplaceTypeNormalizer
from app.services.normalization.job_normalizer import JobNormalizer


def test_location_normalization():
    cleaned, std = LocationNormalizer.normalize("Bangalore, India")
    assert std == "Bengaluru, India"

    cleaned, std_rem = LocationNormalizer.normalize("Remote - India")
    assert std_rem == "Remote, India"


def test_employment_type_normalization():
    assert EmploymentTypeNormalizer.normalize("full-time") == "FULL_TIME"
    assert EmploymentTypeNormalizer.normalize("contractor") == "CONTRACT"
    assert EmploymentTypeNormalizer.normalize("internship") == "INTERNSHIP"
    assert EmploymentTypeNormalizer.normalize("unknown string") == "UNKNOWN"


def test_workplace_type_normalization():
    assert WorkplaceTypeNormalizer.normalize("work from home") == "REMOTE"
    assert WorkplaceTypeNormalizer.normalize("hybrid") == "HYBRID"
    assert WorkplaceTypeNormalizer.normalize("onsite") == "ONSITE"


def test_job_normalizer():
    raw_payload = {
        "external_id": "RAW-01",
        "title": " Senior QA Engineer ",
        "company": " Tech Corp ",
        "location": "Bangalore",
        "employment_type": "fulltime",
        "workplace_type": "hybrid",
        "salary_min": "100000",
        "salary_max": "130000",
    }

    norm = JobNormalizer.normalize_raw_job(raw_payload)
    assert norm["title"] == "Senior QA Engineer"
    assert norm["company_name"] == "Tech Corp"
    assert norm["normalized_location"] == "Bengaluru, India"
    assert norm["employment_type"] == "FULL_TIME"
    assert norm["workplace_type"] == "HYBRID"
    assert norm["salary_min"] == 100000.0


def test_job_normalizer_malformed():
    with pytest.raises(ValueError, match="missing job title"):
        JobNormalizer.normalize_raw_job({"company": "Acme"})

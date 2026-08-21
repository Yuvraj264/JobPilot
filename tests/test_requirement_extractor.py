import pytest
from app.models.job import Job
from app.services.tailoring.requirement_extractor import JobRequirementExtractor, RequirementCategory


def test_requirement_extraction():
    job = Job(
        title="Junior QA Engineer",
        company_name="Acme Technologies",
        source_metadata={
            "required_skills": ["Python", "SQL", "Selenium", "PostgreSQL"],
            "preferred_skills": ["Docker", "AWS"]
        }
    )

    reqs = JobRequirementExtractor.extract_requirements(job)
    req_names = [r["name"] for r in reqs]

    assert "Python" in req_names
    assert "Selenium" in req_names
    assert "PostgreSQL" in req_names
    assert "Docker" in req_names

    categories = {r["name"]: r["category"] for r in reqs}
    assert categories["Python"] == RequirementCategory.PROGRAMMING_LANGUAGE
    assert categories["PostgreSQL"] == RequirementCategory.DATABASE
    assert categories["Selenium"] == RequirementCategory.TESTING_TECHNOLOGY

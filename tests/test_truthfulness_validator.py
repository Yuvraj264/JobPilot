import pytest
from app.models.profile import UserProfile, Skill, Project
from app.models.resume import Resume, ResumeExperience
from app.services.tailoring.truthfulness_validator import ResumeTruthfulnessValidator


def test_fabrication_test_1_unsupported_skill_cypress():
    """
    Test 1 (Requirement 34): Profile lacks Cypress. Job requires Cypress.
    Tailored resume must NOT introduce Cypress into skills.
    """
    profile = UserProfile(
        full_name="Truthful Candidate",
        email="truth@example.com",
        skills=[Skill(name="Python"), Skill(name="Selenium")]
    )

    doc_invalid = {
        "header": {"full_name": "Truthful Candidate", "email": "truth@example.com"},
        "summary": "Experienced QA",
        "skills": [{"name": "Python"}, {"name": "Selenium"}, {"name": "Cypress"}],
        "projects": [],
        "experience": []
    }

    res = ResumeTruthfulnessValidator.validate_tailored_resume(doc_invalid, profile)
    assert res["valid"] is False
    assert any("Cypress" in issue for issue in res["issues"])


def test_fabrication_test_2_no_work_experience_fabricated():
    """
    Test 2 (Requirement 34): Candidate has 0 work experience in master profile/resume.
    Tailored resume must NOT fabricate professional experience.
    """
    profile = UserProfile(
        full_name="Student Candidate",
        email="student@example.com",
        skills=[Skill(name="Python")]
    )

    doc_invalid = {
        "header": {"full_name": "Student Candidate", "email": "student@example.com"},
        "summary": "QA Engineer",
        "skills": [{"name": "Python"}],
        "projects": [],
        "experience": [{"company": "Fake Tech Corp", "role": "Senior QA Engineer"}]
    }

    res = ResumeTruthfulnessValidator.validate_tailored_resume(doc_invalid, profile)
    assert res["valid"] is False
    assert any("FABRICATED WORK EXPERIENCE" in issue for issue in res["issues"])


def test_fabrication_test_3_unsupported_jira():
    """
    Test 3 (Requirement 34): Profile lacks Jira.
    Jira remains unsupported and causes validation failure if introduced.
    """
    profile = UserProfile(
        full_name="Truthful Candidate",
        email="truth@example.com",
        skills=[Skill(name="Python")]
    )

    doc_invalid = {
        "header": {"full_name": "Truthful Candidate", "email": "truth@example.com"},
        "summary": "Developer",
        "skills": [{"name": "Python"}, {"name": "Jira"}],
        "projects": [],
        "experience": []
    }

    res = ResumeTruthfulnessValidator.validate_tailored_resume(doc_invalid, profile)
    assert res["valid"] is False
    assert any("Jira" in issue for issue in res["issues"])


def test_fabrication_test_4_valid_supported_resume():
    """
    Verified supported resume passing truthfulness check cleanly.
    """
    profile = UserProfile(
        full_name="Valid Candidate",
        email="valid@example.com",
        skills=[Skill(name="Python"), Skill(name="SQL")],
        projects=[Project(name="Maze Pathfinder", description="Python maze solver", technologies="Python")]
    )

    doc_valid = {
        "header": {"full_name": "Valid Candidate", "email": "valid@example.com"},
        "summary": "Software Professional",
        "skills": [{"name": "Python"}, {"name": "SQL"}],
        "projects": [{"name": "Maze Pathfinder", "description": "Python maze solver", "technologies": "Python"}],
        "experience": []
    }

    res = ResumeTruthfulnessValidator.validate_tailored_resume(doc_valid, profile)
    assert res["valid"] is True
    assert len(res["issues"]) == 0

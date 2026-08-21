import pytest
from app.models.profile import UserProfile, Skill
from app.services.screening.answer_generator import AnswerGenerator
from app.services.screening.taxonomy import QuestionType


def test_anti_fabrication_prevention_aws():
    """
    MANDATORY TRUTHFULNESS SAFEGUARD TEST (Requirement 31):
    Candidate profile has Python skills but NO AWS skills or projects.
    Question: "Describe your AWS experience."
    MUST return INSUFFICIENT_INFORMATION and NOT fabricate experience.
    """
    profile = UserProfile(
        full_name="Truthful Candidate",
        email="truth@example.com",
        years_of_experience=3.0,
        current_role="Backend Developer",
        skills=[Skill(name="Python"), Skill(name="FastAPI"), Skill(name="PostgreSQL")]
    )

    generator = AnswerGenerator()
    res = generator.generate(
        question_text="Describe your AWS experience in production.",
        question_type=QuestionType.EXPERIENCE,
        answer_source="PROFILE_PLUS_RESUME",
        profile=profile,
        job_context={"title": "Cloud Engineer", "company_name": "Acme"}
    )

    assert res["status"] == "INSUFFICIENT_INFORMATION"
    assert res["requires_human"] is True
    assert "no verifiable evidence" in res["reason"].lower() or "aws" in res["reason"].lower()
    assert "I have extensive AWS experience" not in str(res.get("answer", ""))


def test_anti_fabrication_prevention_selenium():
    """
    MANDATORY TRUTHFULNESS SAFEGUARD TEST:
    Candidate profile lacks Selenium project experience.
    Question: "Describe a project where you used Selenium."
    MUST return INSUFFICIENT_INFORMATION.
    """
    profile = UserProfile(
        full_name="Truthful Candidate",
        email="truth@example.com",
        years_of_experience=2.0,
        current_role="QA Analyst",
        skills=[Skill(name="Manual Testing"), Skill(name="Jira")]
    )

    generator = AnswerGenerator()
    res = generator.generate(
        question_text="Describe a project where you used Selenium for test automation.",
        question_type=QuestionType.PROJECT,
        answer_source="PROFILE_PLUS_RESUME",
        profile=profile,
        job_context={"title": "QA Automation Engineer", "company_name": "Acme"}
    )

    assert res["status"] == "INSUFFICIENT_INFORMATION"
    assert res["requires_human"] is True

import pytest
from app.models.profile import UserProfile, Skill
from app.models.job import Job
from app.services.matching.skill_matcher import SkillMatcher


def test_skill_synonym_normalization():
    assert SkillMatcher.normalize_skill_name("js") == "JavaScript"
    assert SkillMatcher.normalize_skill_name("postgres") == "PostgreSQL"
    assert SkillMatcher.normalize_skill_name("py") == "Python"


def test_skill_matcher_evaluation():
    profile = UserProfile()
    profile.skills = [
        Skill(name="Selenium", proficiency="ADVANCED"),
        Skill(name="SQL", proficiency="INTERMEDIATE"),
        Skill(name="Python", proficiency="INTERMEDIATE"),
    ]

    job = Job(
        title="Selenium QA Automation Engineer",
        description="Required skills: Selenium, SQL, API Testing. Preferred: Java, Jira."
    )

    res = SkillMatcher.evaluate(profile, job)
    assert "Selenium" in res["matched_skills"]
    assert "SQL" in res["matched_skills"]
    assert "API Testing" in res["missing_required"]
    assert res["score"] > 50.0

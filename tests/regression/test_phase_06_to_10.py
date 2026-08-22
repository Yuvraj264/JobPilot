import pytest
from sqlalchemy.orm import Session
from app.models.profile import User, UserProfile
from app.models.job import Job
from app.services.screening.question_classifier import QuestionClassifier
from app.services.screening.taxonomy import QuestionType
from app.services.tailoring.requirement_extractor import JobRequirementExtractor
from app.database.connection import SessionLocal

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

def test_phase_06_to_10_regression(db: Session):
    """
    Verifies question classification and resume requirement extraction (Phases 6 to 10).
    """
    # 1. Test Question Classifier
    res = QuestionClassifier.classify_question("How many years of experience do you have with Python?", field_identifier="exp_py")
    assert res["type"] == QuestionType.EXPERIENCE
    assert res["confidence"] >= 0.90

    res_sal = QuestionClassifier.classify_question("What is your expected salary?", field_identifier="salary")
    assert res_sal["type"] == QuestionType.SALARY

    # 2. Test Job Requirement Extraction
    job = Job(
        title="Python Software Engineer",
        company_name="Extractor Inc",
        location="Remote",
        description="Required: Python experience, Django knowledge, Git version control. Preferred: AWS, Docker.",
        source_metadata={"required_skills": ["Python", "Django"], "preferred_skills": ["AWS"]}
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    reqs = JobRequirementExtractor.extract_requirements(job)
    assert len(reqs) > 0
    # Check that Python is in requirements
    req_names = [r["name"].lower() for r in reqs]
    assert any("python" in n or "django" in n for n in req_names)

    # Clean up
    db.delete(job)
    db.commit()

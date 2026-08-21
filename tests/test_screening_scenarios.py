import time
import pytest
from app.database.connection import SessionLocal
from app.models.profile import User, UserProfile, Skill
from app.services.screening.question_processing_service import QuestionProcessingService
from app.services.screening.taxonomy import QuestionType


def test_screening_mock_scenarios():
    db = SessionLocal()
    try:
        unique_email = f"alex.mercer.{int(time.time()*1000)}@example.com"
        user = User(email=unique_email)
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = UserProfile(
            user_id=user.id,
            full_name="Alex Mercer",
            email=unique_email,
            current_city="Bangalore",
            years_of_experience=3.0,
            current_role="QA Engineer",
            skills=[Skill(name="SQL"), Skill(name="Python")]
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        processor = QuestionProcessingService()
        job_ctx = {"title": "Junior QA Engineer", "company_name": "Acme Technologies"}

        # Scenario 1 — Deterministic
        res1 = processor.process_question(db, "What is your current city?", profile, job_ctx, require_human_review=False)
        assert res1["question_type"] == QuestionType.LOCATION
        assert res1["answer_text"] == "Bangalore"

        # Scenario 2 — Motivation / Role Interest
        res2 = processor.process_question(db, "Why are you interested in this role?", profile, job_ctx, require_human_review=False)
        assert res2["question_type"] == QuestionType.ROLE_INTEREST
        assert "Acme" in res2["answer_text"] or "QA" in res2["answer_text"]

        # Scenario 3 — Missing Experience (Anti-Fabrication)
        res3 = processor.process_question(db, "Describe your experience managing a QA team.", profile, job_ctx, require_human_review=False)
        assert res3["status"] in ["INSUFFICIENT_INFORMATION", "NEEDS_REVIEW"]
        assert res3["requires_human"] is True

        # Scenario 4 — Technical Knowledge
        res4 = processor.process_question(db, "What is regression testing?", profile, job_ctx, require_human_review=False)
        assert res4["question_type"] == QuestionType.TECHNICAL
        assert "regression testing" in res4["answer_text"].lower()

        # Scenario 5 — Personal Experience Missing
        res5 = processor.process_question(db, "Describe a project where you used Selenium.", profile, job_ctx, require_human_review=False)
        assert res5["status"] == "INSUFFICIENT_INFORMATION"

        # Scenario 6 — Character Limit (max 100 chars)
        res6 = processor.process_question(db, "Why this role? (Max 100 characters)", profile, job_ctx, max_length=100, require_human_review=False)
        assert len(res6["answer_text"]) <= 100

        # Scenario 7 — Ambiguous (Low Confidence)
        res7 = processor.process_question(db, "What makes you stand out from other candidates?", profile, job_ctx, require_human_review=False)
        assert res7["status"] == "NEEDS_REVIEW"
        assert res7["requires_human"] is True

        # Scenario 8 — Sensitive Sponsorship
        res8 = processor.process_question(db, "Do you require visa sponsorship?", profile, job_ctx, require_human_review=False)
        assert res8["question_type"] == QuestionType.SPONSORSHIP

    finally:
        db.close()

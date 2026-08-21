import pytest
from app.services.screening.question_classifier import QuestionClassifier
from app.services.screening.taxonomy import QuestionType


def test_question_classifier_taxonomy():
    # Relocation
    c1 = QuestionClassifier.classify_question("Are you willing to relocate?")
    assert c1["type"] == QuestionType.RELOCATION
    assert c1["confidence"] >= 0.95

    # Salary
    c2 = QuestionClassifier.classify_question("What is your expected salary?")
    assert c2["type"] == QuestionType.SALARY
    assert c2["confidence"] >= 0.95

    # Role Interest
    c3 = QuestionClassifier.classify_question("Why are you interested in this role?")
    assert c3["type"] == QuestionType.ROLE_INTEREST
    assert c3["confidence"] >= 0.90

    # Sensitive Work Authorization
    c4 = QuestionClassifier.classify_question("Do you require visa sponsorship?")
    assert c4["type"] == QuestionType.SPONSORSHIP
    assert c4["is_sensitive"] is True

    # Ambiguous question -> Low confidence
    c5 = QuestionClassifier.classify_question("What makes you different?")
    assert c5["confidence"] < 0.70

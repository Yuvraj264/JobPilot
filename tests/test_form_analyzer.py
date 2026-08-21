import pytest
from app.services.automation.form_analyzer import FormAnalyzer
from app.services.automation.profile_field_mapper import ProfileFieldMapper
from app.models.profile import UserProfile


def test_form_analyzer_classification():
    assert FormAnalyzer.classify_field({"label": "Email Address", "input_type": "email"}) == "EMAIL"
    assert FormAnalyzer.classify_field({"label": "Mobile Number", "name": "candidate_phone"}) == "PHONE"
    assert FormAnalyzer.classify_field({"label": "Upload Resume", "input_type": "file"}) == "RESUME"
    assert FormAnalyzer.classify_field({"tag_name": "textarea", "label": "Why are you interested in this role?"}) == "SCREENING_QUESTION"


def test_profile_field_mapper_populated_and_missing():
    # 1. Populated Profile
    profile = UserProfile(
        full_name="Alex Mercer",
        email="alex@example.com",
        phone="+15550199",
        years_of_experience=3.0
    )
    m_email = ProfileFieldMapper.map_field("EMAIL", profile)
    assert m_email["status"] == "MATCHED"
    assert m_email["value"] == "alex@example.com"
    assert m_email["confidence"] == 0.99

    # 2. Unpopulated / Missing Data Profile
    empty_profile = UserProfile(full_name="John Doe")
    m_phone = ProfileFieldMapper.map_field("PHONE", empty_profile)
    assert m_phone["status"] == "MISSING_DATA"
    assert m_phone["confidence"] == 0.0

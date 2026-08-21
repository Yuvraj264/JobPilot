import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_invalid_email_validation():
    """Test that invalid email format is rejected."""
    payload = {
        "full_name": "Test User",
        "email": "not-an-email-address",
        "years_of_experience": 2.0
    }
    res = client.post("/api/profile", json=payload)
    assert res.status_code == 422  # Unprocessable Entity


def test_negative_years_of_experience_rejected():
    """Test that negative years of experience is rejected."""
    payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        "years_of_experience": -1.5
    }
    res = client.post("/api/profile", json=payload)
    assert res.status_code == 422


def test_invalid_education_dates_rejected():
    """Test that end year before start year is rejected."""
    payload = {
        "institution": "Tech College",
        "degree": "B.S.",
        "start_year": 2022,
        "end_year": 2018
    }
    res = client.post("/api/profile/education", json=payload)
    assert res.status_code == 422


def test_invalid_salary_range_rejected():
    """Test that min salary > max salary is rejected."""
    payload = {
        "min_expected_salary": 150000.0,
        "max_expected_salary": 100000.0,
        "salary_currency": "USD"
    }
    res = client.put("/api/profile/preferences/job", json=payload)
    assert res.status_code == 422


def test_invalid_certification_dates_rejected():
    """Test that certification expiry date before issue date is rejected."""
    payload = {
        "name": "AWS Solutions Architect",
        "issuing_organization": "Amazon",
        "issue_date": "2025-01",
        "expiry_date": "2023-01"
    }
    res = client.post("/api/profile/certifications", json=payload)
    assert res.status_code == 422

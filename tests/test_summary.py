import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_profile_summary_endpoint():
    """Test retrieving structured compact profile summary."""
    # Ensure profile exists via seed
    client.post("/api/profile/seed")

    res = client.get("/api/profile/summary")
    assert res.status_code == 200
    data = res.json()
    assert "name" in data
    assert "roles" in data
    assert "locations" in data
    assert "skills" in data
    assert "experience_years" in data
    assert "education_count" in data
    assert "projects_count" in data
    assert "certifications_count" in data
    assert "profile_completeness" in data

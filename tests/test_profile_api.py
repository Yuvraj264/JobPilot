import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_and_get_profile():
    """Test profile creation and retrieval."""
    payload = {
        "full_name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+1-555-0100",
        "current_city": "Austin",
        "current_country": "USA",
        "professional_summary": "Experienced Software Engineer",
        "years_of_experience": 4.0,
        "current_role": "Backend Engineer",
        "employment_status": "Employed"
    }

    # Create profile
    res_create = client.post("/api/profile", json=payload)
    assert res_create.status_code == 201
    data_create = res_create.json()
    assert data_create["full_name"] == "Jane Doe"
    assert data_create["email"] == "jane.doe@example.com"

    # Get profile
    res_get = client.get("/api/profile")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["full_name"] == "Jane Doe"
    assert data_get["years_of_experience"] == 4.0


def test_update_profile():
    """Test updating basic profile info."""
    update_payload = {
        "current_role": "Senior Backend Engineer",
        "years_of_experience": 5.0
    }
    res = client.put("/api/profile", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["current_role"] == "Senior Backend Engineer"
    assert data["years_of_experience"] == 5.0


def test_education_crud():
    """Test adding, listing, updating, and deleting education entries."""
    edu_payload = {
        "institution": "MIT",
        "degree": "B.S.",
        "field_of_study": "Computer Science",
        "start_year": 2017,
        "end_year": 2021,
        "grade_or_cgpa": "3.9"
    }
    # Add
    res_add = client.post("/api/profile/education", json=edu_payload)
    assert res_add.status_code == 201
    edu_id = res_add.json()["id"]

    # List
    res_list = client.get("/api/profile/education")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # Update
    res_update = client.put(f"/api/profile/education/{edu_id}", json={"degree": "B.S. Computer Science"})
    assert res_update.status_code == 200
    assert res_update.json()["degree"] == "B.S. Computer Science"

    # Delete
    res_del = client.delete(f"/api/profile/education/{edu_id}")
    assert res_del.status_code == 204


def test_skills_crud():
    """Test skill management endpoints."""
    skill_payload = {
        "name": "Python",
        "category": "Programming",
        "proficiency": "Expert",
        "years_of_experience": 4.5
    }
    res_add = client.post("/api/profile/skills", json=skill_payload)
    assert res_add.status_code == 201
    skill_id = res_add.json()["id"]

    res_list = client.get("/api/profile/skills")
    assert res_list.status_code == 200

    res_update = client.put(f"/api/profile/skills/{skill_id}", json={"proficiency": "Master"})
    assert res_update.status_code == 200
    assert res_update.json()["proficiency"] == "Master"

    res_del = client.delete(f"/api/profile/skills/{skill_id}")
    assert res_del.status_code == 204


def test_projects_crud():
    """Test project portfolio endpoints."""
    proj_payload = {
        "name": "E-commerce Engine",
        "description": "High performance online store engine",
        "technologies": ["Python", "FastAPI", "PostgreSQL"],
        "project_url": "https://example.com/project"
    }
    res_add = client.post("/api/profile/projects", json=proj_payload)
    assert res_add.status_code == 201
    proj_id = res_add.json()["id"]

    res_del = client.delete(f"/api/profile/projects/{proj_id}")
    assert res_del.status_code == 204


def test_certifications_crud():
    """Test certification endpoints."""
    cert_payload = {
        "name": "CKAD",
        "issuing_organization": "CNCF",
        "issue_date": "2024-01",
        "expiry_date": "2026-01"
    }
    res_add = client.post("/api/profile/certifications", json=cert_payload)
    assert res_add.status_code == 201
    cert_id = res_add.json()["id"]

    res_del = client.delete(f"/api/profile/certifications/{cert_id}")
    assert res_del.status_code == 204


def test_preferences_crud():
    """Test updating job & application preferences."""
    job_pref_payload = {
        "target_roles": ["Software Engineer", "DevOps Engineer"],
        "preferred_locations": ["Remote", "Austin"],
        "work_arrangements": ["remote"],
        "employment_types": ["full-time"],
        "min_expected_salary": 90000.0,
        "max_expected_salary": 130000.0,
        "salary_currency": "USD"
    }
    res_job = client.put("/api/profile/preferences/job", json=job_pref_payload)
    assert res_job.status_code == 200
    assert res_job.json()["min_expected_salary"] == 90000.0

    app_pref_payload = {
        "min_job_match_score": 80.0,
        "max_applications_per_day": 20,
        "require_approval_before_submission": True
    }
    res_app = client.put("/api/profile/preferences/application", json=app_pref_payload)
    assert res_app.status_code == 200
    assert res_app.json()["require_approval_before_submission"] is True

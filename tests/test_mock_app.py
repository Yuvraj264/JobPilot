import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_mock_application_pages():
    # 1. Step 1 Personal Info
    res1 = client.get("/mock/apply/101/step/1")
    assert res1.status_code == 200
    assert "Full Name" in res1.text
    assert "candidate_email" in res1.text

    # 2. Step 2 Education & Experience
    res2 = client.get("/mock/apply/101/step/2")
    assert res2.status_code == 200
    assert "Highest Degree Qualification" in res2.text

    # 3. Step 3 Preferences & Resume & Screening Questions
    res3 = client.get("/mock/apply/101/step/3")
    assert res3.status_code == 200
    assert "Upload Resume" in res3.text
    assert "Screening Questions" in res3.text

    # 4. Step 4 Review Page
    res_rev = client.get("/mock/apply/101/review")
    assert res_rev.status_code == 200
    assert "READY_FOR_REVIEW" in res_rev.text

    # 5. Mock CAPTCHA Page
    res_cap = client.get("/mock/apply/101/captcha")
    assert res_cap.status_code == 200
    assert "CAPTCHA" in res_cap.text

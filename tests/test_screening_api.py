import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_screening_api_lifecycle():
    # 1. Post Analyze Question
    res_ana = client.post("/api/questions/analyze", json={"question_text": "Are you willing to relocate?"})
    assert res_ana.status_code == 200
    data_ana = res_ana.json()
    assert data_ana["question_type"] == "RELOCATION"

    # 2. Get Pending Review Questions
    res_rev = client.get("/api/questions/review")
    assert res_rev.status_code == 200
    assert isinstance(res_rev.json(), list)

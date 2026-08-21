import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_tailoring_api_endpoints():
    # 1. List Tailored Resumes
    res_tr = client.get("/api/tailored-resumes")
    assert res_tr.status_code == 200
    assert isinstance(res_tr.json(), list)

    # 2. List Application Packages
    res_pkg = client.get("/api/application-packages")
    assert res_pkg.status_code == 200
    assert isinstance(res_pkg.json(), list)

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_completeness_calculation_and_seed():
    """Test seeding sample dev profile and calculating completeness percentage."""
    # Seed full sample profile
    res_seed = client.post("/api/profile/seed")
    assert res_seed.status_code == 201

    # Check completeness
    res_comp = client.get("/api/profile/completeness")
    assert res_comp.status_code == 200
    data = res_comp.json()
    assert "percentage" in data
    assert isinstance(data["percentage"], int)
    assert data["percentage"] > 70

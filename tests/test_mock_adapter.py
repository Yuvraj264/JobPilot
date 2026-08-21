import pytest
from app.services.adapters.mock import MockJobSourceAdapter
from app.services.adapters.linkedin import LinkedInJobSourceAdapter


def test_mock_adapter_discovery():
    adapter = MockJobSourceAdapter()
    assert adapter.source_name() == "mock"
    assert adapter.health_check() in ["healthy", True]

    jobs = adapter.discover_jobs(limit=10, page=1)
    assert len(jobs) == 10
    assert jobs[0]["external_id"] == "MOCK-101"

    # Page 2
    jobs_p2 = adapter.discover_jobs(limit=10, page=2)
    assert len(jobs_p2) >= 5
    assert jobs_p2[0]["external_id"] != jobs[0]["external_id"]


def test_placeholder_adapters_raise():
    link_ad = LinkedInJobSourceAdapter()
    with pytest.raises(NotImplementedError):
        link_ad.discover_jobs()

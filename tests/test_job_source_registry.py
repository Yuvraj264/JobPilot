import pytest
from app.services.adapters.registry import JobSourceRegistry
from app.services.adapters.mock import MockJobSourceAdapter
from app.services.adapters.linkedin import LinkedInJobSourceAdapter


def test_job_source_registry():
    reg = JobSourceRegistry()
    mock_ad = MockJobSourceAdapter()
    link_ad = LinkedInJobSourceAdapter()

    reg.register(mock_ad, enabled_by_default=True)
    reg.register(link_ad, enabled_by_default=False)

    assert reg.get("mock") is not None
    assert reg.get("LINKEDIN") is not None
    assert reg.get("unknown") is None

    assert reg.is_enabled("mock") is True
    assert reg.is_enabled("linkedin") is False

    reg.disable("mock")
    assert reg.is_enabled("mock") is False

    reg.enable("linkedin")
    assert reg.is_enabled("linkedin") is True

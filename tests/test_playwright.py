import pytest
from browser import verify_browser_launch
from app.services.adapters.company_careers import run_async


def test_playwright_launch():
    """
    Test Playwright browser launcher in headless mode.
    """
    success = run_async(verify_browser_launch(headless=True))
    assert success is True, "Playwright browser launch failed"

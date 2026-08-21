import pytest
from browser import verify_browser_launch


@pytest.mark.asyncio
async def test_playwright_launch():
    """
    Test Playwright browser launcher in headless mode.
    """
    success = await verify_browser_launch(headless=True)
    assert success is True, "Playwright browser launch failed"

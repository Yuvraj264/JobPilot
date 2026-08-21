import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Playwright, Page


class BrowserManager:
    """
    Browser Manager utilizing Playwright Python API.
    Provides basic browser lifecycle management for future automation steps.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def start(self) -> Browser:
        """
        Starts the Playwright Chromium browser instance.
        """
        if not self._browser:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )
        return self._browser

    async def close(self) -> None:
        """
        Closes browser and stops Playwright engine.
        """
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def new_page(self) -> Page:
        """
        Opens a new page tab in the browser context.
        """
        browser = await self.start()
        context = await browser.new_context()
        return await context.new_page()


async def verify_browser_launch(headless: bool = True) -> bool:
    """
    Utility verification function to confirm Playwright browser launch capability.
    """
    manager = BrowserManager(headless=headless)
    try:
        browser = await manager.start()
        page = await manager.new_page()
        await page.goto("about:blank")
        title = await page.title()
        await manager.close()
        return True
    except Exception as e:
        print(f"Browser launch failed: {e}")
        await manager.close()
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_browser_launch(headless=True))
    print(f"Browser Launch Verification: {'SUCCESS' if success else 'FAILED'}")

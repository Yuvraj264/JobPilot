"""
JobPilot Agent Placeholder.
Phase 1: Shell structure for high-level browser agent controller.
"""

from browser import BrowserManager


class JobPilotAgent:
    """
    Minimal agent structure for future browser application workflows.
    """

    def __init__(self, headless: bool = True):
        self.browser_manager = BrowserManager(headless=headless)

    async def initialize(self):
        """Initializes the browser context."""
        await self.browser_manager.start()

    async def shutdown(self):
        """Closes browser session."""
        await self.browser_manager.close()

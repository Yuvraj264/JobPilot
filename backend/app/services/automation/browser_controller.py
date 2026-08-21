import os
import uuid
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, ElementHandle

SCREENSHOT_DIR = os.path.abspath("./storage/screenshots")


class BrowserController:
    """
    Centralized Playwright Browser Controller wrapping Chromium instance, page navigation,
    DOM evaluation, screenshot capture, and state inspection.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    def start(self):
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(viewport={"width": 1280, "height": 800})
            self.page = self.context.new_page()

    def stop(self):
        if self.page:
            try: self.page.close()
            except Exception: pass
        if self.context:
            try: self.context.close()
            except Exception: pass
        if self.browser:
            try: self.browser.close()
            except Exception: pass
        if self.playwright:
            try: self.playwright.stop()
            except Exception: pass
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def navigate(self, url: str):
        if not self.page:
            self.start()
        self.page.goto(url, wait_until="domcontentloaded", timeout=15000)

    def current_url(self) -> str:
        return self.page.url if self.page else ""

    def page_title(self) -> str:
        return self.page.title() if self.page else ""

    def capture_screenshot(self, name_prefix: str = "shot") -> str:
        if not self.page:
            return ""
        filename = f"{name_prefix}_{uuid.uuid4().hex[:6]}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        self.page.screenshot(path=filepath, full_page=True)
        return filepath

    def get_dom_html(self) -> str:
        return self.page.content() if self.page else ""

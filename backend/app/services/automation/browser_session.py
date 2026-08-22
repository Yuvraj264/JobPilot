from typing import List, Optional
from urllib.parse import urlparse
import logging
from app.services.automation.browser_controller import BrowserController

logger = logging.getLogger(__name__)


class DomainValidationError(Exception):
    pass


class ApplicationBrowserSession:
    """
    Manages browser session, allowed domain security checks, and redirect tracking.
    """
    def __init__(self, allowed_domains: List[str], headless: bool = True):
        self.allowed_domains = [d.lower() for d in allowed_domains]
        self.controller = BrowserController(headless=headless)
        self.redirect_chain: List[str] = []
        self.original_url: Optional[str] = None
        self.final_url: Optional[str] = None

    def start(self):
        self.controller.start()

    def stop(self):
        self.controller.stop()

    @property
    def page(self):
        return self.controller.page

    def navigate(self, url: str) -> str:
        self.validate_url(url)
        self.original_url = url
        self.redirect_chain = [url]

        self.controller.navigate(url)

        final_url = self.controller.current_url()
        self.final_url = final_url
        if final_url and final_url != url:
            self.redirect_chain.append(final_url)
            self.validate_url(final_url)

        return final_url

    def validate_url(self, url: str):
        from app.services.url_security_service import URLSecurityService
        try:
            URLSecurityService.validate_url(url, self.allowed_domains)
        except ValueError as err:
            raise DomainValidationError(str(err))

    def current_url(self) -> str:
        return self.controller.current_url()

    def page_title(self) -> str:
        return self.controller.page_title()

    def capture_screenshot(self, name_prefix: str = "shot") -> str:
        return self.controller.capture_screenshot(name_prefix)

    def get_dom_html(self) -> str:
        return self.controller.get_dom_html()

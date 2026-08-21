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
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            raise DomainValidationError(f"Invalid URL scheme: '{parsed.scheme}'. Only HTTP/HTTPS allowed.")

        domain = parsed.netloc.lower()
        if ":" in domain:
            domain = domain.split(":")[0]

        # Safety fallback for local synthetic site testing
        if domain in ["localhost", "127.0.0.1"]:
            return

        is_allowed = False
        for allowed in self.allowed_domains:
            allowed_clean = allowed.lower()
            if allowed_clean.startswith("*."):
                suffix = allowed_clean[2:]
                if domain == suffix or domain.endswith("." + suffix):
                    is_allowed = True
                    break
            elif domain == allowed_clean:
                is_allowed = True
                break

        if not is_allowed:
            raise DomainValidationError(f"Navigation to domain '{domain}' is blocked by allowed domain safety constraints.")

    def current_url(self) -> str:
        return self.controller.current_url()

    def page_title(self) -> str:
        return self.controller.page_title()

    def capture_screenshot(self, name_prefix: str = "shot") -> str:
        return self.controller.capture_screenshot(name_prefix)

    def get_dom_html(self) -> str:
        return self.controller.get_dom_html()

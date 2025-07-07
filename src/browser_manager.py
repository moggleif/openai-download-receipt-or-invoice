import logging
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Connects to an existing browser (you started with --remote-debugging-port)
    and hands you its first live page.
    """

    def __init__(self, cfg):
        self.port = int(cfg.remote_debugging_port)
        self._pw = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None

    def connect(self) -> Page:
        logger.info("Starting Playwright → attaching to port %d", self.port)
        self._pw = sync_playwright().start()
        endpoint = f"http://localhost:{self.port}"
        self.browser = self._pw.chromium.connect_over_cdp(endpoint)
        logger.info("✓ Attached to browser (version=%s)", self.browser.version)

        # Reuse the first context
        if not self.browser.contexts:
            raise RuntimeError("No contexts available in attached browser")
        self.context = self.browser.contexts[0]
        logger.info("Reusing context with %d pages", len(self.context.pages))

        # Reuse the first non-closed page, or create a new one
        for p in self.context.pages:
            if not p.is_closed():
                self.page = p
                logger.info("Reusing existing page: %s", p.url)
                break
        else:
            logger.info("No open pages—creating one at %s", self.openai_home_url)
            self.page = self.context.new_page()
            self.page.goto(cfg.openai_home_url)
            self.page.wait_for_load_state("networkidle")
            logger.info("Navigated new page to %s", self.openai_home_url)

        # Remember where we started
        self._original_url = self.page.url
        logger.info("Attached to page at %s", self._original_url)

        return self.page

    def close(self):
        # Restore the original URL before detaching
        if self.page and self._original_url:
            try:
                logger.info("Restoring original page URL: %s", self._original_url)
                self.page.goto(self._original_url)
                self.page.wait_for_load_state("networkidle")
            except Exception as e:
                logger.warning("Could not restore original URL: %s", e)

        # Finally stop Playwright (does not close your real browser)
        if self._pw:
            logger.info("Stopping Playwright (leaving browser open)")
            self._pw.stop()

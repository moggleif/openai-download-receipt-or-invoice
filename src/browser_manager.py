import logging
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Error as PlaywrightError

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Connects to an existing browser (you started with --remote-debugging-port)
    and hands you its first live page.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.port = int(cfg.remote_debugging_port)
        self._pw = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None

    def connect_over_cdp(self) -> Page:
        logger.info("Starting Playwright → attaching to port %d", self.port)
        self._pw = sync_playwright().start()
        endpoint = f"http://localhost:{self.port}"

        # Try CDP connection if an endpoint was given
        try:
            self.browser = self._pw.chromium.connect_over_cdp(endpoint)
            logger.debug("→ Connected to existing browser via CDP.")
        except PlaywrightError:
            logger.debug("⚠ Failed to connect via CDP. Launching new browser for manual login...")
            return None

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
            logger.info("No open pages—creating one at %s", self.cfg.openai_home_url)
            self.page = self.context.new_page()

        # Remember where we started
        self._original_url = self.page.url
        logger.info("Attached to page at %s", self._original_url)

        # Check if logged in
        self.page.goto(self.cfg.openai_home_url)
        self.page.wait_for_load_state("networkidle")
        logger.info("Navigated new page to %s", self.cfg.openai_home_url)

        # Check for something only visible when logged in.
        sidebar = self.page.locator("button:has-text('sidebar')")
        if sidebar.count() > 0:
            logger.debug("Detected button – already logged in")
            return self.page

        # Fallback: → treat as not logged in
        return None
    
    def close_cdp(self):
        # Restore the original URL before detaching
        if self.page and self._original_url:
            try:
                logger.info("Restoring original page URL: %s", self._original_url)
                self.page.goto(self._original_url)
                self.page.wait_for_load_state("networkidle")
            except Exception as e:
                logger.warning("Could not restore original URL: %s", e)
        logger.info("Leaving browser open")
        # Finally stop Playwright
        if self._pw:
            logger.info("Stopping Playwright")
            self._pw.stop()


    def start_browser(self) -> Page:

        """
        Starts Playwright and opens a browser context.
        """
        logger.debug("Start a Browser with playwright")
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        )
        self.page = self._context.new_page()
        logger.debug("Browser and context started")
        self.page.goto(self.cfg.openai_home_url)
        self.page.wait_for_load_state("networkidle")
        
        return self.page
    
    def close_browser(self):
        """
        Closes the browser.
        """
        if self._browser:
            self._browser.close()
        logger.debug("Browser stopped")
        # Finally stop Playwright
        if self._pw:
            logger.info("Stopping Playwright")
            self._pw.stop()       

    def close(self):
        if self._running_over_cdp:
            self.close_cdp()
        else:
            self.close_browser()

    def get_page(self) -> Page:
        # First, try to connect over CDP
        self._running_over_cdp = True
        self.page = self.connect_over_cdp()
        if self.page == None:
            self.close_cdp()
            self._running_over_cdp = False
            self.page = self.start_browser()
        
        return self.page


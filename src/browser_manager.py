import logging
from playwright.sync_api import (
    sync_playwright, Browser, BrowserContext, Page,
    Error as PlaywrightError,
)

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Connects to an existing browser via CDP (--remote-debugging-port)
    or launches a new one as fallback.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.port = int(cfg.remote_debugging_port)
        self._pw = None
        self._browser: Browser = None
        self._context: BrowserContext = None
        self._page: Page = None
        self._original_url = None
        self._using_cdp = False

    # ── public API ───────────────────────────────────────────────

    def __enter__(self) -> Page:
        self._page = self._connect_cdp()
        if self._page:
            self._using_cdp = True
            return self._page

        self._stop_playwright()
        self._page = self._launch_browser()
        return self._page

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._using_cdp:
            self._close_cdp()
        else:
            self._close_browser()
        return False

    # ── private ──────────────────────────────────────────────────

    def _connect_cdp(self) -> Page | None:
        logger.info("Connecting to browser on port %d via CDP...", self.port)
        self._pw = sync_playwright().start()

        if not self._attach_to_browser():
            return None

        self._pick_or_create_page()
        return self._page

    def _attach_to_browser(self) -> bool:
        try:
            self._browser = self._pw.chromium.connect_over_cdp(f"http://localhost:{self.port}")
        except PlaywrightError:
            logger.warning("CDP connection failed — will launch a new browser")
            return False

        logger.info("Attached to browser (version=%s)", self._browser.version)

        if not self._browser.contexts:
            raise RuntimeError("No browser contexts available")
        self._context = self._browser.contexts[0]
        return True

    def _pick_or_create_page(self):
        for p in self._context.pages:
            if not p.is_closed():
                self._page = p
                break
        else:
            self._page = self._context.new_page()

        self._original_url = self._page.url
        logger.info("Using page at %s", self._original_url)

    def _close_cdp(self):
        if self._page and self._original_url:
            try:
                logger.info("Restoring original page: %s", self._original_url)
                self._page.goto(self._original_url)
                self._page.wait_for_load_state("networkidle")
            except Exception as e:
                logger.warning("Could not restore original URL: %s", e)
        self._stop_playwright()

    def _launch_browser(self) -> Page:
        logger.info("Launching new browser...")
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            ),
        )
        self._page = self._context.new_page()
        return self._page

    def _close_browser(self):
        if self._browser:
            self._browser.close()
        self._stop_playwright()

    def _stop_playwright(self):
        if self._pw:
            self._pw.stop()
            self._pw = None


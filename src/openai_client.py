import logging
import re
import time
import random
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

class OpenAIClient:
    """
    Assists with login to ChatGPT and downloading the latest receipt PDF.
    Fields are filled automatically; user manually clicks buttons.
    Verbose logging throughout.
    """
    HOME_URL = "https://chatgpt.com"
    AUTH_URL_PATTERN = "**auth.openai.com/log-in**"
    SETTINGS_URL = "https://chatgpt.com/#settings/Account"
    MANAGE_BUTTON = "button:has-text('Manage')"
    SESSION_URL_PATTERN = re.compile(r"https://pay\.openai\.com/p/session/live")
    INVOICE_LINK_SELECTOR = "a[href^='https://invoice.stripe.com/i/']"
    STRIPE_URL_PATTERN = "https://invoice.stripe.com**"
    DOWNLOAD_BUTTON = "text=Download invoice"

    def __init__(self, cfg):
        self.cfg = cfg
        logger.debug("OpenAIClient initialized with cfg=%s", cfg)
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None

    def start(self):
        """
        Starts Playwright and opens a browser context.
        """
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
        self._page = self._context.new_page()
        logger.debug("Browser and context started")

    def login(self):
        """
        Assisted login flow:
        1. Navigate to ChatGPT home
        2. User clicks 'Log in' manually
        3. Script waits for auth page
        4. Script fills email; user clicks Continue
        5. Script fills password; user clicks Continue
        6. Script fills MFA code; user clicks Continue
        """
        if not self._page:
            self.start()

        logger.info("Starting assisted login process")
        # Step 1: Go to home
        self._page.goto(self.HOME_URL)
        self._page.wait_for_load_state('networkidle')
        logger.debug("Page loaded, waiting for 'Log in' button")


        delay = random.uniform(1,5)
        logger.debug("Sleeping %.2f seconds before going to login page", delay)
        time.sleep(delay)
        buttons = self._page.query_selector_all('button')
        logger.debug("Found %d buttons on the page", len(buttons))
        for idx, btn in enumerate(buttons):
            try:
                text = btn.inner_text().strip()
            except Exception:
                text = '<unable to retrieve text>'
            logger.debug("Button %d: '%s'", idx, text)
        # Click the second 'Log in' button
        self._page.locator("button:has-text('Log in')").nth(1).click()
        
        # Step 2: Fill email
        logger.debug("Automatically filling email: %s", self.cfg.openai_email)
        self._page.fill('input[type="email"]', self.cfg.openai_email)
        delay = random.uniform(1,5)
        logger.debug("Sleeping %.2f seconds before email submit", delay)
        time.sleep(delay)
        self._page.click('button[type="submit"]')        

        # Step 3: Fill password
        self._page.wait_for_selector('input[type="password"]', timeout=60000)
        logger.debug("Automatically filling password")
        self._page.fill('input[type="password"]', self.cfg.openai_password)
        delay = random.uniform(1,5)
        logger.debug("Sleeping %.2f seconds before password submit", delay)
        time.sleep(delay)
        self._page.click("button:has-text('Continue')")

        # Step 4: Fill MFA code
        logger.debug("Manually filling MFA")
        
        # Confirm login success
        self._page.wait_for_url(self.HOME_URL + '/*', timeout=120000)
        logger.info("Login successful, current page: %s", self._page.url)

    def download_latest_receipt(self, output_path: str):
        """
        Automates downloading the latest receipt:
        1. Navigate to Settings, user clicks 'Manage'
        2. Wait for session URL
        3. Click first invoice link
        4. Wait for Stripe page, click download, save PDF
        """
        if not self._page:
            raise RuntimeError("Call login() before download_latest_receipt()")
        page = self._page
        logger.info("Starting receipt download")

        # Settings & Manage
        page.goto(self.SETTINGS_URL)
        logger.debug("Waiting for 'Manage' button to be available: %s", self.MANAGE_BUTTON)
        page.wait_for_selector(self.MANAGE_BUTTON, timeout=60000)
        # Auto-click the correct Manage button (billing) - select the second instance if multiple exist
        logger.debug("Clicking 'Manage' button: %s (billing)", self.MANAGE_BUTTON)
        # There may be multiple 'Manage' buttons; pick the second one for billing
        page.locator(self.MANAGE_BUTTON).nth(1).click()
        # Wait for invoice links to appear
        logger.debug("Waiting for invoice link selector: %s", self.INVOICE_LINK_SELECTOR)
        page.wait_for_selector(self.INVOICE_LINK_SELECTOR, timeout=60000)


        # Click the first Stripe invoice link
        links = page.query_selector_all(self.INVOICE_LINK_SELECTOR)
        if not links:
            raise RuntimeError("No Stripe invoice links found on session page")
        first_link = links[0]
        href = first_link.get_attribute('href')
        logger.debug("Clicking Stripe invoice link: %s", href)
        with page.expect_popup() as popup_info:
            first_link.click()

        # Load invoice page
        invoice_page = popup_info.value
        logger.info("Wait for invoice page to load.")
        invoice_page.wait_for_selector(self.DOWNLOAD_BUTTON, timeout=60000)
        logger.info("Invoice page loaded: %s", invoice_page.url)

        # Step 4: Click download and save
        with invoice_page.expect_download() as download_info:
            logger.debug("Clicking download button: %s", self.DOWNLOAD_BUTTON)
            invoice_page.click(self.DOWNLOAD_BUTTON)
        download = download_info.value
        download.save_as(output_path)
        logger.info("Invoice saved to %s", output_path)


    def close(self):
        """
        Closes the browser and stops Playwright.
        """
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
        logger.debug("Browser and Playwright stopped")

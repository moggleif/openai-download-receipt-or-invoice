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

    def __init__(self, cfg, page):
        self.cfg = cfg
        logger.debug("OpenAIClient initialized with cfg=%s", cfg)
        self._pw = None
        self._browser = None
        self._context = None
        self._page = page

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
        # Load invoice page

        invoice_url = first_link.get_attribute("href")
        invoice_page = page  # we’re reusing the same tab
        invoice_page.goto(invoice_url)        
        #with page.context.expect_page() as page_info:
        #    first_link.click()
        #invoice_page = page_info.value

        #with page.expect_popup() as popup_info:
#            first_link.click()


 #       invoice_page = popup_info.value
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

    def is_logged_in(self) -> bool:
        """
        Returns True if we appear to be already logged in to ChatGPT.
        It does this by navigating to the home URL and looking
        for the absence of a 'Log in' button (and presence of
        the chat sidebar).
        """
        if not self._page:
            self.start_or_connect()

        # Go to the ChatGPT home page
        self._page.goto(self.HOME_URL)
        self._page.wait_for_load_state("networkidle")

        # If there's a login button visible, we're not logged in
        login_buttons = self._page.locator("button:has-text('Log in')")
        try:
            if login_buttons.count() > 0:
                logger.debug("Detected 'Log in' button – not logged in yet")
                return False
        except Exception:
            # any error finding the button, assume not logged in
            return False

        # Otherwise, check for something only visible when logged in,
        # e.g. the chat list sidebar
        sidebar = self._page.locator("nav[aria-label='Chat sidebar']")
        if sidebar.count() > 0:
            logger.debug("Detected chat sidebar – already logged in")
            return True

        # Fallback: no login button, no sidebar → treat as not logged in
        return False

    def ensure_logged_in(self):
        """
        Wrapper that only runs login() if we’re not already authenticated.
        """
        if not self.is_logged_in():
            logger.info("Not logged in; invoking login()")
            self.login()
        else:
            logger.info("Already logged in; skipping login()")

    def start_or_connect(self):
        """
        Launch a Chromium-based browser. If self.cfg.user_data_dir is set,
        reuse that profile via launch_persistent_context(); otherwise open
        a fresh context. Uses self.cfg.browser_executable_path if provided.
        Always opens a new page and navigates to HOME_URL.
        """
        # Read config values
        profile = getattr(self.cfg, "user_data_dir", None)
        exe = getattr(self.cfg, "browser_executable_path", None)
        logger.debug(
            "Configuration → user_data_dir=%s, browser_executable_path=%s",
            profile, exe
        )

        # Start Playwright
        logger.info("Starting Playwright engine")
        self._pw = sync_playwright().start()

        # Prepare launch args
        launch_args = {"headless": False, "args": ["--disable-blink-features=AutomationControlled"]}
        if exe:
            launch_args["executable_path"] = exe
            logger.debug("Added executable_path to launch_args: %s", exe)
        logger.debug("Final launch_args: %r", launch_args)

        # Launch browser (persistent or fresh)
        if profile:
            logger.info("Launching persistent context with profile: %s", profile)
            self._context = self._pw.chromium.launch_persistent_context(
                user_data_dir=profile,
                **launch_args
            )
            self._browser = self._context.browser
        else:
            logger.info("Launching new browser instance")
            self._browser = self._pw.chromium.launch(**launch_args)
            self._context = self._browser.new_context()

        # Log the Chromium version (property, not method)
        logger.info("Browser launched; Chromium version=%s", self._browser.version)

        # Always open a new page
        logger.info("Creating a new page in the browser context")
        self._page = self._context.new_page()
        logger.info("New page created: %s", self._page)

        # Navigate to home so you see something
        logger.info("Navigating new page to %s", self.HOME_URL)
        self._page.goto(self.HOME_URL)
        self._page.wait_for_load_state("networkidle")
        logger.info("Page loaded; browser should now be visible")

        # Final diagnostics
        logger.debug("After new_page(), context.pages count=%d", len(self._context.pages))
        logger.info("start_or_connect complete – browser window is up and at HOME_URL")

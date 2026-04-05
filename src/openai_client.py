import logging
import re
import time
import random
import base64
import threading

logger = logging.getLogger(__name__)

class OpenAIClient:
    """
    Assists with login to ChatGPT and downloading the latest receipt PDF.
    Fields are filled automatically; user manually clicks buttons.
    Verbose logging throughout.
    """
    AUTH_URL_PATTERN = "**auth.openai.com/log-in**"
    SETTINGS_URL = "https://chatgpt.com/#settings/Account"
    MANAGE_BUTTON = "button:has-text('Manage')"
    SESSION_URL_PATTERN = re.compile(r"https://pay\.openai\.com/p/session/live")
    INVOICE_LINK_SELECTOR = "a[href^='https://invoice.stripe.com/i/']"
    STRIPE_URL_PATTERN = "https://invoice.stripe.com**"
    DOWNLOAD_BUTTON = "text=Download receipt"

    def __init__(self, cfg, page):
        self.cfg = cfg
        logger.debug("OpenAIClient initialized with cfg=%s", cfg)
        self._pw = None
        self._browser = None
        self._context = None
        self._page = page

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
        self._page.goto(self.cfg.openai_home_url)
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
        self._page.wait_for_selector('input[type="email"]', timeout=60000)        
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
        self._page.wait_for_url(self.cfg.openai_home_url + '/*', timeout=120000)
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

        # 2) Find all 'Manage' buttons and click the last one
        manage_buttons = page.locator(self.MANAGE_BUTTON)
        count = manage_buttons.count()
        logger.info("Found %d 'Manage' button(s) on settings page", count)

        if count == 0:
            raise RuntimeError("No 'Manage' buttons found on settings page")

        # Heuristic: the billing/subscription manage is usually the last one
        logger.info("Clicking last 'Manage' button (index %d)", count - 1)
        manage_buttons.nth(count - 1).click()
        
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
        logger.info("Wait for invoice page to load.")
        invoice_page.wait_for_selector(self.DOWNLOAD_BUTTON, timeout=60000)
        logger.info("Invoice page loaded: %s", invoice_page.url)

        # Step 4: Click "Download receipt" and get the PDF
        # The button is a <span> that triggers JS which calls
        # invoicedata.stripe.com/invoice_receipt_file_url/... to get the
        # actual PDF URL, then navigates to it. We intercept that API
        # response to get the PDF URL, then fetch the PDF in-browser.
        pdf_url_holder = {}
        url_ready = threading.Event()

        def on_response(response):
            url = response.url
            if "invoice_receipt_file_url" in url:
                try:
                    body = response.json()
                    logger.debug("invoice_receipt_file_url response: %s", body)
                    # The response should contain the PDF file URL
                    file_url = body.get("file_url") or body.get("url")
                    if file_url:
                        logger.info("Got PDF file URL: %s", file_url)
                        pdf_url_holder["url"] = file_url
                        url_ready.set()
                    else:
                        logger.warning("No file URL in response: %s", body)
                except Exception as e:
                    logger.warning("Failed to parse receipt URL response: %s", e)

        page.on("response", on_response)
        logger.debug("Clicking download button: %s", self.DOWNLOAD_BUTTON)
        invoice_page.click(self.DOWNLOAD_BUTTON)

        if not url_ready.wait(timeout=30):
            page.remove_listener("response", on_response)
            raise RuntimeError("Timed out waiting for PDF URL from invoicedata.stripe.com")

        page.remove_listener("response", on_response)
        pdf_url = pdf_url_holder["url"]

        # Fetch the PDF inside the browser context (has cookies/session)
        logger.info("Fetching PDF via in-browser fetch(): %s", pdf_url)
        pdf_b64 = invoice_page.evaluate("""async (url) => {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const buf = await resp.arrayBuffer();
            const bytes = new Uint8Array(buf);
            let binary = '';
            for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
            return btoa(binary);
        }""", pdf_url)

        pdf_bytes = base64.b64decode(pdf_b64)
        if not pdf_bytes[:5] == b"%PDF-":
            raise RuntimeError(f"Downloaded file is not a valid PDF (header: {pdf_bytes[:20]!r})")

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        logger.info("Invoice saved to %s (%d bytes)", output_path, len(pdf_bytes))

    def is_logged_in(self) -> bool:
        """
        Returns True if we appear to be already logged in to ChatGPT.
        It does this by navigating to the home URL and looking
        for the absence of a 'Log in' button (and presence of
        the chat sidebar).
        """
        # Go to the ChatGPT home page
        self._page.goto(self.cfg.openai_home_url)
        self._page.wait_for_load_state("networkidle")
        logger.info("Navigated page to %s", self.cfg.openai_home_url)

        buttons = self._page.query_selector_all('button')
        logger.debug("Found %d buttons on the page", len(buttons))
        for idx, btn in enumerate(buttons):
            try:
                text = btn.inner_text().strip()
            except Exception:
                text = '<unable to retrieve text>'
            logger.debug("Button %d: '%s'", idx, text)

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
        sidebar = self._page.locator("button:has-text('sidebar')")
        if sidebar.count() > 0:
            logger.debug("Detected buttons – already logged in")
            return True

        # Fallback: → treat as logged in
        return True

    def ensure_logged_in(self):
        """
        Wrapper that only runs login() if we’re not already authenticated.
        """
       
        if self.is_logged_in():
            logger.info("Already logged in; skipping login()")
        else:
            logger.info("Not logged in; invoking login()")
            self.login()
            
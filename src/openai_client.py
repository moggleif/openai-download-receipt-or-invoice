import logging
import os
import glob
import time
import random

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Handles login to ChatGPT and downloading the latest receipt PDF.
    """
    SETTINGS_URL = "https://chatgpt.com/#settings/Account"
    MANAGE_BUTTON = "button:has-text('Manage')"
    INVOICE_LINK_SELECTOR = "a[href^='https://invoice.stripe.com/i/']"
    DOWNLOAD_BUTTON = "text=Download receipt"

    LOGIN_BUTTON = "button:has-text('Log in')"
    EMAIL_INPUT = 'input[type="email"]'
    PASSWORD_INPUT = 'input[type="password"]'
    SUBMIT_BUTTON = 'button[type="submit"]'
    CONTINUE_BUTTON = "button:has-text('Continue')"

    def __init__(self, cfg, page):
        self.cfg = cfg
        self._page = page

    def ensure_logged_in(self):
        if self._is_logged_in():
            logger.info("Already logged in")
        else:
            logger.info("Not logged in — starting login flow")
            self._login()

    def download_latest_receipt(self, output_path: str):
        """Navigate to billing, open the latest invoice, and download the PDF."""
        self._navigate_to_billing()
        invoice_url = self._get_latest_invoice_url()
        self._open_invoice(invoice_url)
        self._download_pdf(output_path)

    # ── private ──────────────────────────────────────────────────

    def _navigate_to_billing(self):
        """Open settings and click the billing Manage button."""
        page = self._page
        page.goto(self.SETTINGS_URL)
        page.wait_for_selector(self.MANAGE_BUTTON, timeout=60000)

        manage_buttons = page.locator(self.MANAGE_BUTTON)
        count = manage_buttons.count()
        logger.info("Found %d 'Manage' button(s)", count)
        if count == 0:
            raise RuntimeError("No 'Manage' buttons found on settings page")
        manage_buttons.nth(count - 1).click()

    def _get_latest_invoice_url(self) -> str:
        """Wait for invoice links and return the URL of the most recent one."""
        page = self._page
        page.wait_for_selector(self.INVOICE_LINK_SELECTOR, timeout=60000)
        links = page.query_selector_all(self.INVOICE_LINK_SELECTOR)
        if not links:
            raise RuntimeError("No Stripe invoice links found")
        url = links[0].get_attribute("href")
        logger.info("Latest invoice: %s", url)
        return url

    def _open_invoice(self, invoice_url: str):
        """Navigate to the Stripe invoice page."""
        self._page.goto(invoice_url)
        self._page.wait_for_selector(self.DOWNLOAD_BUTTON, timeout=60000)

    def _download_pdf(self, output_path: str):
        """Click the download button and save the PDF to output_path."""
        download_dir = os.path.abspath(os.path.dirname(output_path) or ".")
        new_pdf = self._trigger_download(download_dir)
        self._save_pdf(new_pdf, output_path)

    def _trigger_download(self, download_dir: str) -> str:
        """Start the download via CDP and wait for the PDF to appear."""
        cdp_session = self._set_cdp_download_path(download_dir)
        pdfs_before = set(glob.glob(os.path.join(download_dir, "*.pdf")))
        self._page.click(self.DOWNLOAD_BUTTON)
        new_pdf = self._wait_for_new_pdf(download_dir, pdfs_before)
        cdp_session.detach()
        if not new_pdf:
            raise RuntimeError(f"No PDF appeared in {download_dir} after clicking download")
        return new_pdf

    def _save_pdf(self, source: str, output_path: str):
        """Rename the downloaded PDF to the desired output path."""
        if os.path.abspath(source) != os.path.abspath(output_path):
            os.rename(source, output_path)
        logger.info("Receipt saved to %s (%d bytes)", output_path, os.path.getsize(output_path))

    def _set_cdp_download_path(self, download_dir: str):
        """Configure the browser to save downloads to download_dir via CDP."""
        cdp_session = self._page.context.new_cdp_session(self._page)
        cdp_session.send("Browser.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": download_dir,
        })
        logger.info("CDP download path: %s", download_dir)
        return cdp_session

    def _login(self):
        """Assisted login: fills email/password, user handles MFA manually."""
        page = self._page
        page.goto(self.cfg.openai_home_url)
        page.wait_for_load_state("networkidle")

        self._human_delay()
        page.locator(self.LOGIN_BUTTON).nth(1).click()

        self._fill_field(self.EMAIL_INPUT, self.cfg.openai_email, self.SUBMIT_BUTTON)
        self._fill_field(self.PASSWORD_INPUT, self.cfg.openai_password, self.CONTINUE_BUTTON)

        # Wait for MFA + redirect (up to 5 minutes)
        page.wait_for_url(self.cfg.openai_home_url + "/*", timeout=300000)
        logger.info("Login successful")

    def _fill_field(self, selector: str, value: str, submit_selector: str):
        """Wait for a form field, fill it, and click the submit button."""
        self._page.wait_for_selector(selector, timeout=60000)
        self._page.fill(selector, value)
        self._human_delay()
        self._page.click(submit_selector)

    def _is_logged_in(self) -> bool:
        page = self._page
        page.goto(self.cfg.openai_home_url)
        page.wait_for_load_state("networkidle")

        try:
            return page.locator(self.LOGIN_BUTTON).count() == 0
        except Exception:
            return False

    @staticmethod
    def _wait_for_new_pdf(directory, existing, timeout=60):
        """Poll for a new PDF file in *directory* that wasn't in *existing*."""
        for _ in range(timeout):
            time.sleep(1)
            new_file = OpenAIClient._find_new_pdf(directory, existing)
            if new_file:
                return new_file
        return None

    @staticmethod
    def _find_new_pdf(directory, existing):
        """Return a fully written new PDF, or None if nothing yet."""
        current = set(glob.glob(os.path.join(directory, "*.pdf")))
        new_files = current - existing
        if not new_files:
            return None
        path = new_files.pop()
        return OpenAIClient._wait_until_written(path)

    @staticmethod
    def _wait_until_written(path):
        """Block until the file size stabilizes."""
        prev_size = -1
        while True:
            size = os.path.getsize(path)
            if size == prev_size and size > 0:
                return path
            prev_size = size
            time.sleep(0.5)

    @staticmethod
    def _human_delay():
        time.sleep(random.uniform(1, 3))

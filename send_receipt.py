#!/usr/bin/env python
"""Automated OpenAI Receipt Mailer — downloads the latest receipt and emails it."""
import logging
import datetime

from dotenv import load_dotenv
from src.config import Config
from src.openai_client import OpenAIClient
from src.email_client import EmailClient
from src.browser_manager import BrowserManager


def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger = logging.getLogger(__name__)

    load_dotenv()
    cfg = Config()

    date_str = datetime.date.today().strftime("%Y-%m-%d")
    pdf_path = f"openai_receipt_{date_str}.pdf"

    browser = BrowserManager(cfg)
    page = browser.get_page()

    try:
        client = OpenAIClient(cfg, page)
        client.ensure_logged_in()
        client.download_latest_receipt(pdf_path)
        logger.info("Receipt downloaded successfully")
    finally:
        browser.close()

    EmailClient(cfg).send(pdf_path)
    logger.info("Receipt emailed to %s", cfg.recipient)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Automated OpenAI Receipt Mailer — downloads the latest receipt and emails it."""
import logging
import datetime

from dotenv import load_dotenv
from src.config import Config
from src.openai_client import OpenAIClient
from src.email_client import EmailClient
from src.browser_manager import BrowserManager


def configure_logging_and_config() -> tuple[logging.Logger, Config]:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    load_dotenv()
    return logging.getLogger(__name__), Config()


def todays_receipt_filename() -> str:
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    return f"openai_receipt_{date_str}.pdf"


def download_latest_receipt(cfg: Config, pdf_path: str) -> None:
    with BrowserManager(cfg) as page:
        client = OpenAIClient(cfg, page)
        client.ensure_logged_in()
        client.download_latest_receipt(pdf_path)


def email_receipt(cfg: Config, pdf_path: str) -> None:
    EmailClient(cfg).send(pdf_path)


def main() -> None:
    logger, cfg = configure_logging_and_config()
    pdf_path = todays_receipt_filename()

    download_latest_receipt(cfg, pdf_path)
    logger.info("Receipt downloaded successfully")

    email_receipt(cfg, pdf_path)
    logger.info("Receipt emailed to %s", cfg.recipient)


if __name__ == "__main__":
    main()

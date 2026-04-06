#!/usr/bin/env python
"""Downloads the latest OpenAI receipt and emails it."""
import logging
import datetime

from dotenv import load_dotenv
from src.config import Config
from src.receipt_downloader import ReceiptDownloader
from src.receipt_mailer import ReceiptMailer
from src.browser_session import BrowserSession


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
    with BrowserSession(cfg) as page:
        downloader = ReceiptDownloader(cfg, page)
        downloader.ensure_logged_in()
        downloader.download_latest_receipt(pdf_path)


def email_receipt(cfg: Config, pdf_path: str) -> None:
    ReceiptMailer(cfg).send(pdf_path)


def main() -> None:
    logger, cfg = configure_logging_and_config()
    pdf_path = todays_receipt_filename()

    download_latest_receipt(cfg, pdf_path)
    logger.info("Receipt downloaded successfully")

    email_receipt(cfg, pdf_path)
    logger.info("Receipt emailed to %s", cfg.recipient)


if __name__ == "__main__":
    main()

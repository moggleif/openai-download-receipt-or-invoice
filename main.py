#!/usr/bin/env python
"""Downloads the latest OpenAI receipt and emails it."""
import argparse
import logging
import datetime

from dotenv import load_dotenv
from src.config import Config
from src.logging_setup import setup_logging
from src.receipt_downloader import ReceiptDownloader
from src.receipt_mailer import ReceiptMailer
from src.browser_session import BrowserSession


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and email OpenAI receipt")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show debug output in console")
    return parser.parse_args()


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
    args = parse_args()
    setup_logging(verbose=args.verbose)
    load_dotenv()

    logger = logging.getLogger(__name__)
    cfg = Config()
    pdf_path = todays_receipt_filename()

    download_latest_receipt(cfg, pdf_path)
    logger.info("Receipt downloaded to %s", pdf_path)

    email_receipt(cfg, pdf_path)
    logger.info("Receipt emailed to %s — all done", cfg.recipient)


if __name__ == "__main__":
    main()

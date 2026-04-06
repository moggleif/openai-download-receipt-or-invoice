#!/usr/bin/env python
"""Downloads the latest OpenAI receipt and emails it."""
import argparse
import logging
import datetime

from dotenv import load_dotenv
from src.config import Config
from src.receipt_downloader import ReceiptDownloader
from src.receipt_mailer import ReceiptMailer
from src.browser_session import BrowserSession


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and email OpenAI receipt")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show debug output in console")
    return parser.parse_args()


def configure_logging_and_config(verbose: bool = False) -> tuple[logging.Logger, Config]:
    log_format = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

    import sys
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)

    logfile = logging.FileHandler("openai_receipt.log")
    logfile.setLevel(logging.DEBUG)

    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[console, logfile],
    )
    for name in ("asyncio", "playwright", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)
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
    args = parse_args()
    logger, cfg = configure_logging_and_config(verbose=args.verbose)
    pdf_path = todays_receipt_filename()

    download_latest_receipt(cfg, pdf_path)
    logger.info("Receipt downloaded to %s", pdf_path)

    email_receipt(cfg, pdf_path)
    logger.info("Receipt emailed to %s — all done", cfg.recipient)


if __name__ == "__main__":
    main()

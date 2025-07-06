#!/usr/bin/env python
"""
Entry point for the Automated OpenAI Receipt Mailer
"""
import logging
import datetime

from dotenv import load_dotenv
from src.config import Config
from src.openai_client import OpenAIClient
from src.email_client import EmailClient


def main() -> None:
    # Configure verbose logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.debug("Starting Automated OpenAI Receipt Mailer...")
    
    # This will read .env into os.environment
    load_dotenv()   

    # Load configuration and validate environment variables
    cfg = Config()
    logger.debug("Configuration loaded: %s", cfg)

    # Create a timestamped filename for the receipt PDF
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    pdf_path = f"openai_receipt_{date_str}.pdf"
    logger.debug("PDF path set to %s", pdf_path)

    # Download the latest receipt and send via email
    ai_client = OpenAIClient(cfg)
    ai_client.login()
    ai_client.download_latest_receipt(pdf_path)
    logger.debug("Receipt downloaded successfully")

    mail_client = EmailClient(cfg)
    mail_client.send(pdf_path)
    logger.debug("Receipt emailed successfully to %s", cfg.recipient)

    logger.debug("Process completed.")


if __name__ == '__main__':
    main()

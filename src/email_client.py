import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class EmailClient:
    """Sends an email with the receipt PDF attached, then deletes the file."""

    def __init__(self, cfg):
        self.cfg = cfg

    def send(self, pdf_path: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = "Your OpenAI Receipt"
        msg["From"] = self.cfg.smtp_email
        msg["To"] = self.cfg.recipient
        msg.set_content("Hi there,\n\nPlease find your latest OpenAI receipt attached.\n")

        try:
            with open(pdf_path, "rb") as f:
                msg.add_attachment(
                    f.read(),
                    maintype="application",
                    subtype="pdf",
                    filename=os.path.basename(pdf_path),
                )

            host, port = self.cfg.smtp_host, self.cfg.smtp_port

            if port == 465:
                logger.info("Connecting to %s:%s over SSL", host, port)
                server = smtplib.SMTP_SSL(host, port)
            else:
                logger.info("Connecting to %s:%s with STARTTLS", host, port)
                server = smtplib.SMTP(host, port)
                server.ehlo()
                server.starttls()

            server.login(self.cfg.smtp_user, self.cfg.smtp_password)
            server.send_message(msg)
            server.quit()
            logger.info("Email sent to %s", self.cfg.recipient)
        except Exception:
            logger.exception("Failed to send email")
            raise
        finally:
            try:
                os.remove(pdf_path)
                logger.debug("Deleted %s", pdf_path)
            except OSError as e:
                logger.warning("Could not delete %s: %s", pdf_path, e)

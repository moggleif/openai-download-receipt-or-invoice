import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class ReceiptMailer:
    """Sends an email with the receipt PDF attached, then deletes the file."""

    def __init__(self, cfg):
        self.cfg = cfg

    # ── public API ───────────────────────────────────────────────

    def send(self, pdf_path: str) -> None:
        msg = self._build_message(pdf_path)
        try:
            self._smtp_send(msg)
        except Exception:
            logger.exception("Failed to send email")
            raise
        finally:
            self._cleanup(pdf_path)

    # ── private ──────────────────────────────────────────────────

    def _build_message(self, pdf_path: str) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = "Your OpenAI Receipt"
        msg["From"] = self.cfg.smtp_email
        msg["To"] = self.cfg.recipient
        msg.set_content("Hi there,\n\nPlease find your latest OpenAI receipt attached.\n")
        with open(pdf_path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename=os.path.basename(pdf_path),
            )
        return msg

    def _connect(self) -> smtplib.SMTP:
        host, port = self.cfg.smtp_host, self.cfg.smtp_port
        if port == 465:
            logger.info("Connecting to SMTP server %s:%s (SSL)", host, port)
            server = smtplib.SMTP_SSL(host, port)
        else:
            logger.info("Connecting to SMTP server %s:%s (STARTTLS)", host, port)
            server = smtplib.SMTP(host, port)
            server.ehlo()
            server.starttls()
        server.login(self.cfg.smtp_user, self.cfg.smtp_password)
        return server

    def _smtp_send(self, msg: EmailMessage) -> None:
        server = self._connect()
        server.send_message(msg)
        server.quit()
        logger.info("Email with receipt sent to %s", self.cfg.recipient)

    def _cleanup(self, pdf_path: str) -> None:
        try:
            os.remove(pdf_path)
            logger.debug("Deleted %s", pdf_path)
        except OSError as e:
            logger.warning("Could not delete %s: %s", pdf_path, e)

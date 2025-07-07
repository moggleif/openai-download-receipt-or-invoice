import logging
import smtplib
import os
from email.message import EmailMessage

logger = logging.getLogger(__name__)

class EmailClient:
    """
    Sends an email with the receipt attached over SSL or TLS based on configuration.
    Deletes the PDF file after attempting to send, regardless of success.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        logger.debug("EmailClient initialized with cfg=%s", cfg)

    def send(self, pdf_path: str) -> None:
        msg = EmailMessage()
        msg['Subject'] = 'Your OpenAI Receipt'
        msg['From']    = self.cfg.smtp_email
        msg['To']      = self.cfg.recipient
        msg.set_content(
            'Hi there,\n\nPlease find your latest OpenAI receipt attached.\n'
        )

        # Attach PDF
        try:
            with open(pdf_path, 'rb') as f:
                msg.add_attachment(
                    f.read(), maintype='application', subtype='pdf', filename=os.path.basename(pdf_path)
                )

            host = self.cfg.smtp_host
            port = self.cfg.smtp_port
            user = self.cfg.smtp_user
            pwd  = self.cfg.smtp_password

            # Choose SSL (port 465) or TLS (others)
            if port == 465:
                logger.info("Connecting to SMTP server %s:%s over SSL", host, port)
                server = smtplib.SMTP_SSL(host, port)
            else:
                logger.info("Connecting to SMTP server %s:%s with STARTTLS", host, port)
                server = smtplib.SMTP(host, port)
                server.ehlo()
                server.starttls()

            server.login(user, pwd)
            server.send_message(msg)
            server.quit()
            logger.info("Email sent to %s", self.cfg.recipient)
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            raise
        finally:
            try:
                os.remove(pdf_path)
                logger.debug("Deleted PDF file: %s", pdf_path)
            except Exception as rm_err:
                logger.warning("Could not delete PDF file %s: %s", pdf_path, rm_err)

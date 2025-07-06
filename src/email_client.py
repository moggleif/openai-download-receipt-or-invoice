import smtplib
from email.message import EmailMessage
import os
import logging

class EmailClient:
    def __init__(self, cfg):
        self.cfg = cfg

    def send(self, pdf_path: str) -> None:
        msg = EmailMessage()
        msg['Subject'] = 'Your OpenAI Receipt'
        msg['From']    = self.cfg.smtp_user
        msg['To']      = self.cfg.recipient
        msg.set_content('Please find your latest OpenAI receipt attached.')

        with open(pdf_path, 'rb') as f:
            msg.add_attachment(
                f.read(),
                maintype='application',
                subtype='pdf',
                filename=os.path.basename(pdf_path)
            )

        with smtplib.SMTP(self.cfg.smtp_host, self.cfg.smtp_port) as smtp:
            smtp.starttls()
            smtp.login(self.cfg.smtp_user, self.cfg.smtp_password)
            smtp.send_message(msg)

        logging.info("Receipt emailed to %s", self.cfg.recipient)

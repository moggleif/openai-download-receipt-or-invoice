import os
import logging

logger = logging.getLogger(__name__)

class Config:
    REQUIRED_VARS = [
        'OPENAI_EMAIL', 'OPENAI_PASSWORD',
        'RECIPIENT_EMAIL', 'SMTP_HOST',
        'SMTP_USER', 'SMTP_EMAIL', 'SMTP_PASSWORD'
    ]

    def __init__(self):
        missing = [v for v in self.REQUIRED_VARS if not os.getenv(v)]
        if missing:
            raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")

        self.openai_email    = os.getenv('OPENAI_EMAIL')
        self.openai_password = os.getenv('OPENAI_PASSWORD')
        self.remote_debugging_port  = os.getenv('OPENAI_REMOTE_DEBUG_PORT')
        self.user_data_dir    = os.getenv('OPENAI_USER_DATA_DIR')
        self.browser_executable_path  = os.getenv('OPENAI_BROWSER_EXE_PATH')
        self.recipient       = os.getenv('RECIPIENT_EMAIL')
        self.smtp_host       = os.getenv('SMTP_HOST')
        self.smtp_port       = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user       = os.getenv('SMTP_USER')
        self.smtp_email       = os.getenv('SMTP_EMAIL')
        self.smtp_password   = os.getenv('SMTP_PASSWORD')

        if not os.path.isfile(self.browser_executable_path):
            logger.error("Browser executable not found at %s", self.browser_executable_path)

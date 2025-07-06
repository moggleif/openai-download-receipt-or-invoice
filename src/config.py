import os

class Config:
    REQUIRED_VARS = [
        'OPENAI_EMAIL', 'OPENAI_PASSWORD',
        'RECIPIENT_EMAIL', 'SMTP_HOST',
        'SMTP_USER', 'SMTP_PASSWORD'
    ]

    def __init__(self):
        missing = [v for v in self.REQUIRED_VARS if not os.getenv(v)]
        if missing:
            raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")

        self.openai_email    = os.getenv('OPENAI_EMAIL')
        self.openai_password = os.getenv('OPENAI_PASSWORD')
        self.recipient       = os.getenv('RECIPIENT_EMAIL')
        self.smtp_host       = os.getenv('SMTP_HOST')
        self.smtp_port       = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user       = os.getenv('SMTP_USER')
        self.smtp_password   = os.getenv('SMTP_PASSWORD')

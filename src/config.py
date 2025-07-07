import os

class Config:
    REQUIRED_VARS = [
        'OPENAI_HOME_URL',
        'RECIPIENT_EMAIL', 'SMTP_HOST', 'SMTP_PORT',
        'SMTP_USER', 'SMTP_EMAIL', 'SMTP_PASSWORD'
    ]

    def __init__(self):
        missing = [v for v in self.REQUIRED_VARS if not os.getenv(v)]
        if missing:
            raise EnvironmentError(f"Missing required env vars: {', '.join(missing)}")

        # Required settings
        self.openai_home_url       = os.getenv('OPENAI_HOME_URL')
        self.recipient             = os.getenv('RECIPIENT_EMAIL')
        self.smtp_host             = os.getenv('SMTP_HOST')
        self.smtp_port             = int(os.getenv('SMTP_PORT'))
        self.smtp_user             = os.getenv('SMTP_USER')
        self.smtp_email            = os.getenv('SMTP_EMAIL')
        self.smtp_password         = os.getenv('SMTP_PASSWORD')

        # Optional settings
        self.openai_email          = os.getenv('OPENAI_EMAIL', '')  # defaults to empty if unset
        self.openai_password       = os.getenv('OPENAI_PASSWORD', '')  # defaults to empty if unset
        self.remote_debugging_port = os.getenv('BROWSER_REMOTE_DEBUG_PORT', '9222')  # optional
# Automated OpenAI Receipt Emailer

This repository contains a Python script that automatically logs into your OpenAI account, downloads the most recent receipt PDF, and emails it to a specified address. You can schedule the script to run monthly (or at any interval) to automate your billing workflow.

## Features

* Headless login to OpenAI via Playwright
* Retrieval of the latest receipt PDF from your billing dashboard
* SMTP email delivery of the receipt as a PDF attachment
* Easy configuration via environment variables
* MANUAL fill in One-time-password for MFA used by Open AI

## Prerequisites

* Python 3.7 or higher
* [Playwright](https://playwright.dev/) for browser automation
* Access to an SMTP server (e.g., Gmail, SendGrid, Mailgun)

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/openai-receipt-mailer.git
   cd openai-receipt-mailer
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**

   ```bash
   playwright install
   ```

## Configuration

Create a `.env` file in the project root (or export the following environment variables in your shell):

```ini
# OpenAI login
OPENAI_EMAIL=your_email@example.com
OPENAI_PASSWORD=your_openai_password

# Email delivery
RECIPIENT_EMAIL=destination@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=smtp_username
SMTP_PASSWORD=smtp_password
```

> **Tip:** For Gmail, use an App Password and set `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`.

## Usage

Run the script manually to test:

```bash
python send_receipt.py
```

You have two minutes to fill in MFA and press enter. The rest, the script takes care of.
Lots of logs, to see whats going on.
The script takes some time to run, going to fast, Open AI believes your are running a script...

## Security Considerations

* Store your credentials securely (consider using a secrets manager).
* Limit file permissions on the script and downloaded PDFs.
* Use TLS (STARTTLS) for SMTP connections.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

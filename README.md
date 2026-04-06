# OpenAI Receipt Downloader

Downloads the latest receipt PDF from your OpenAI account and emails it as an attachment. Connects to your existing browser session via CDP so you stay logged in — no need to store OpenAI credentials.

## How it works

1. Attaches to your running browser (Vivaldi, Chrome, etc.) via Chrome DevTools Protocol
2. Navigates to ChatGPT Settings > Billing > Manage
3. Opens the latest Stripe invoice and downloads the receipt PDF
4. Emails the PDF to configured recipients via SMTP

## Quick start

### Linux

```bash
chmod +x init.sh && ./init.sh
```

### Windows (PowerShell)

```powershell
.\init.ps1
```

This creates a virtual environment, installs dependencies, and copies `.env.example` and `run.sh.example`/`run.ps1.example` for you to configure.

## Configuration

Edit `.env` with your settings:

```ini
# Required
OPENAI_HOME_URL=https://chatgpt.com
RECIPIENT_EMAIL=destination@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USER=smtp_username
SMTP_EMAIL=sender@example.com
SMTP_PASSWORD=smtp_password

# Optional
BROWSER_REMOTE_DEBUG_PORT=9222
```

## Usage

Start your browser with remote debugging enabled, then run the script:

```bash
./run.sh        # Linux
.\run.ps1       # Windows
```

The run scripts automatically detect if a browser with remote debugging is already running. If not, they start one and close it when done. If a browser is already running, it's reused and left open.

Make sure you're logged in to ChatGPT in the browser. The script attaches to it, downloads the receipt, emails it, and restores your browser tab to where it was.

### Starting the browser manually

If you prefer to manage the browser yourself:

```bash
# Linux (Vivaldi snap)
snap run vivaldi.vivaldi-stable --remote-debugging-port=9222

# Windows (Vivaldi)
Start-Process "$env:LOCALAPPDATA\Vivaldi\Application\vivaldi.exe" "--remote-debugging-port=9222"

# Other Chromium browsers
google-chrome --remote-debugging-port=9222
chromium --remote-debugging-port=9222
```

## Scheduled monthly run (Linux)

Run the installer to set up a systemd user timer that downloads the receipt on the 4th of every month at 10:00. If the computer is off on the 4th, it runs automatically at the next boot.

```bash
./install-schedule.sh
```

Check status and next run time:

```bash
systemctl --user status openai-receipt.timer
systemctl --user list-timers
```

To uninstall:

```bash
systemctl --user disable --now openai-receipt.timer
rm ~/.config/systemd/user/openai-receipt.{service,timer}
systemctl --user daemon-reload
```

## Fallback login

If no browser with remote debugging is available, the script launches a temporary Chromium instance and handles login automatically (fills email/password, you handle MFA within 5 minutes). For this, add to `.env`:

```ini
OPENAI_EMAIL=your_email@example.com
OPENAI_PASSWORD=your_openai_password
```

## Security

- `.env` and `run.sh`/`run.ps1` are gitignored
- Credentials are only in `.env`, never in code
- The script restores your browser tab after running

## License

MIT. See [LICENSE](LICENSE).

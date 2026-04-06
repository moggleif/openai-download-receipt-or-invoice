#!/bin/bash
set -e

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example — fill in your credentials."
else
    echo ".env already exists, skipping."
fi

if [ ! -f run.sh ]; then
    cp run.sh.example run.sh
    chmod +x run.sh
    echo "Created run.sh from run.sh.example — adjust if needed."
else
    echo "run.sh already exists, skipping."
fi

echo "Done! Edit .env, then run ./run.sh"

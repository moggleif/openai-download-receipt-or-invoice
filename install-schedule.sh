#!/bin/bash
# Installs a systemd user timer that runs the receipt downloader
# on the 4th of every month. If the computer is off on the 4th,
# it runs at next boot thanks to Persistent=true.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="openai-receipt"

install_timer() {
    local unit_dir="$HOME/.config/systemd/user"
    mkdir -p "$unit_dir"

    write_service_unit "$unit_dir"
    write_timer_unit "$unit_dir"
    enable_timer
}

write_service_unit() {
    local unit_dir="$1"
    cat > "$unit_dir/$SERVICE_NAME.service" <<EOF
[Unit]
Description=Download OpenAI receipt and email it

[Service]
Type=oneshot
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/run.sh
EOF
    echo "Created $unit_dir/$SERVICE_NAME.service"
}

write_timer_unit() {
    local unit_dir="$1"
    cat > "$unit_dir/$SERVICE_NAME.timer" <<EOF
[Unit]
Description=Monthly OpenAI receipt download (4th of each month)

[Timer]
OnCalendar=*-*-04 10:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
    echo "Created $unit_dir/$SERVICE_NAME.timer"
}

enable_timer() {
    systemctl --user daemon-reload
    systemctl --user enable --now "$SERVICE_NAME.timer"
    echo ""
    echo "Timer enabled. Verify with:"
    echo "  systemctl --user status $SERVICE_NAME.timer"
    echo "  systemctl --user list-timers"
}

install_timer

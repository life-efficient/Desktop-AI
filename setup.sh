#!/bin/bash

REPO_DIR="/home/pi/Desktop-AI"
START_SCRIPT="$REPO_DIR/start.sh"
SERVICE_FILE="desktop-ai.service"
SYSTEMD_PATH="/etc/systemd/system/$SERVICE_FILE"
LOG_FILE="$REPO_DIR/setup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "--- Setup script initiated ---"

# 1. Install system dependencies
apt update
apt install -y vim python3-full python3-venv libportaudio2 libportaudiocpp0 portaudio19-dev

# 2. Set up Python venv and install Python dependencies as pi
sudo -u pi python3 -m venv /home/pi/venv
sudo -u pi /home/pi/venv/bin/pip install --upgrade pip
sudo -u pi /home/pi/venv/bin/pip install -r "$REPO_DIR/requirements.txt"

# 3. Make start.sh executable
chmod +x "$START_SCRIPT"
log "Made start.sh executable."

# 4. Create systemd service file
cat > "$REPO_DIR/$SERVICE_FILE" <<EOL
[Unit]
Description=Desktop-AI Auto Start
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Environment=HOME=/home/pi
Environment=USER=pi
WorkingDirectory=/home/pi/Desktop-AI
ExecStart=/bin/bash /home/pi/Desktop-AI/start.sh
Restart=on-failure
StandardOutput=append:/home/pi/Desktop-AI/startup.log
StandardError=append:/home/pi/Desktop-AI/startup.log

[Install]
WantedBy=multi-user.target
EOL

log "Created $SERVICE_FILE in repo root."

# 5. Copy service file to systemd
cp "$REPO_DIR/$SERVICE_FILE" "$SYSTEMD_PATH"
log "Copied $SERVICE_FILE to $SYSTEMD_PATH."

# 6. Set ownership of all files to pi
chown -R pi:pi /home/pi/Desktop-AI
chown -R pi:pi /home/pi/venv

# 7. Reload systemd, enable and start the service
systemctl daemon-reload
systemctl enable $SERVICE_FILE
systemctl restart $SERVICE_FILE
log "Systemd service enabled and started."

# Set 'preconfigured' connection to priority 20
sudo nmcli connection modify preconfigured connection.autoconnect-priority 20

echo -e "\nWould you like to add a new WiFi network?\nPress Enter to continue, or press Escape to skip."
read -n 1 key
if [[ $key == $'\e' ]]; then
  echo -e "\nSkipping WiFi network addition."
else
  bash /home/pi/Desktop-AI/add_wifi.sh
fi

log "Setup complete."
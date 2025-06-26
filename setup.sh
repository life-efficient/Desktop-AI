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

# Make start.sh executable
chmod +x "$START_SCRIPT"
if [ $? -eq 0 ]; then
    log "Made start.sh executable."
else
    log "ERROR: Failed to make start.sh executable."
    exit 1
fi

# Create systemd service file
cat > "$REPO_DIR/$SERVICE_FILE" <<EOL
[Unit]
Description=Desktop-AI Auto Start
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Desktop-AI
ExecStart=/bin/bash /home/pi/Desktop-AI/start.sh
Restart=on-failure
StandardOutput=append:/home/pi/Desktop-AI/startup.log
StandardError=append:/home/pi/Desktop-AI/startup.log

[Install]
WantedBy=multi-user.target
EOL

log "Created $SERVICE_FILE in repo root."

# Copy service file to systemd
sudo cp "$REPO_DIR/$SERVICE_FILE" "$SYSTEMD_PATH"
if [ $? -eq 0 ]; then
    log "Copied $SERVICE_FILE to $SYSTEMD_PATH."
else
    log "ERROR: Failed to copy $SERVICE_FILE to $SYSTEMD_PATH."
    exit 1
fi

# Reload systemd, enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_FILE
sudo systemctl restart $SERVICE_FILE
log "Systemd service enabled and started."

log "Setup complete."

sudo apt update
apt install vim
# sudo apt install alsa-utils # for audio recording
# arecord -l # shows the available devices

sudo apt install python3-full python3-venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install numpy scipy sounddevice
sudo apt-get install libportaudio2 libportaudiocpp0 portaudio19-dev
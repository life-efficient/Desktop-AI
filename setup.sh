#!/bin/bash

REPO_DIR="$HOME/Desktop-AI"
START_SCRIPT="$REPO_DIR/start.sh"
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

# Add crontab entry if not present
CRON_CMD="@reboot /bin/bash $START_SCRIPT"
crontab -l 2>/dev/null | grep -F "$CRON_CMD" > /dev/null
if [ $? -ne 0 ]; then
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    log "Added @reboot crontab entry."
else
    log "Crontab entry already exists."
fi

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
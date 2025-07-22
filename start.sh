#!/bin/bash

# Set up variables
REPO_DIR="/home/pi/Desktop-AI"
VENV_DIR="/home/pi/venv"
LOGFILE="/home/pi/desktop-ai-logs/startup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

log "--- Startup script initiated ---"

# Ensure repo exists
if [ ! -d "$REPO_DIR/.git" ]; then
    log "ERROR: Repo not found at $REPO_DIR. Exiting."
    exit 1
fi

# Pull latest code
git -C "$REPO_DIR" pull origin main >> "$LOGFILE" 2>&1
sync
if [ $? -ne 0 ]; then
    log "ERROR: git pull failed."
    exit 1
fi
log "Repo updated."

# Ensure venv exists
if [ ! -d "$VENV_DIR" ]; then
    log "Creating Python virtual environment."
    python3 -m venv "$VENV_DIR" >> "$LOGFILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR: venv creation failed."
        exit 1
    fi
fi

# Activate venv
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    log "ERROR: venv activation failed."
    exit 1
fi
log "Virtual environment activated."

# Install dependencies
if [ -f "$REPO_DIR/requirements.txt" ]; then
    pip install --upgrade pip >> "$LOGFILE" 2>&1
    pip install -r "$REPO_DIR/requirements.txt" >> "$LOGFILE" 2>&1
    if [ $? -ne 0 ]; then
        log "ERROR: pip install failed."
        exit 1
    fi
    log "Dependencies installed."
else
    log "WARNING: requirements.txt not found. Skipping dependency install."
fi

# Run main.py
if [ -f "$REPO_DIR/main.py" ]; then
    log "Running main.py."
    python -u "$REPO_DIR/main.py"
    log "main.py finished."
else
    log "ERROR: main.py not found at $REPO_DIR."
    exit 1
fi
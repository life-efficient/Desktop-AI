# Desktop-AI Auto-Start Setup

This project is designed to run automatically on Raspberry Pi startup using a systemd service. The scripts will ensure your code is always up-to-date, dependencies are installed, and your main Python application runs after every boot.

## Setup Instructions

1. **Clone the repository to your home directory:**
   ```sh
   git clone <your-repo-url> ~/Desktop-AI
   cd ~/Desktop-AI
   ```

2. **Run the setup script:**
   ```sh
   bash setup.sh
   ```
   - This will:
     - Make `start.sh` executable
     - Create a `desktop-ai.service` systemd unit file
     - Install and enable the systemd service to run `start.sh` after boot and after the network is online

3. **Reboot to test:**
   ```sh
   sudo reboot
   ```

## What Happens on Boot?
- The `desktop-ai.service` systemd service will:
  1. Wait for the network to be online
  2. Run `start.sh` from your repo directory
  3. `start.sh` will:
     - Pull the latest code from the `main` branch
     - Create and activate a Python virtual environment at `~/venv` if it doesn't exist
     - Install dependencies from `requirements.txt` (if present)
     - Run `main.py` from your repo directory
     - Log all actions to `startup.log` in the repo root

## Logs
- Setup actions: `setup.log`
- Startup actions and errors: `startup.log`

## Managing the Service
- Check status:
  ```sh
  systemctl status desktop-ai.service
  ```
- View logs:
  ```sh
  tail -f ~/Desktop-AI/startup.log
  ```
- Restart the service:
  ```sh
  sudo systemctl restart desktop-ai.service
  ```

## Notes
- Make sure your `main.py` and `requirements.txt` are in the repo root as referenced in the scripts.
- You can edit the scripts to change paths or behavior as needed. 
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
   sudo bash setup.sh
   ```
   - This will:
     - Install all required system and Python dependencies
     - Set up the systemd service to run your app after boot
     - Set the "preconfigured" WiFi connection profile to priority 20 (highest)
     - Prompt you to optionally add a new WiFi network using `nmcli` (press Enter to add, Escape to skip)

3. **Reboot to test:**
   ```sh
   sudo reboot
   ```

## Adding or Modifying WiFi Networks

- All WiFi configuration is now managed via **NetworkManager** (`nmcli`).
- To add a new WiFi network at any time, run:
  ```sh
  bash add_wifi.sh
  ```
  - This will prompt for SSID, password, and optional priority, and add or update the network using `nmcli`.
  - The "preconfigured" network's priority is not changed by this script (only by setup.sh).

- To change the priority of an existing network:
  ```sh
  sudo nmcli connection modify "<ConnectionName>" connection.autoconnect-priority <number>
  ```

## What Happens on Boot?
- The `desktop-ai.service` systemd service will:
  1. Wait for the network to be online
  2. Run `start.sh` from your repo directory
  3. `start.sh` will:
     - Pull the latest code from the `main` branch
     - Create and activate a Python virtual environment at `/home/pi/venv` if it doesn't exist
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
- All WiFi configuration is now managed via `nmcli` and NetworkManager, not wpa_supplicant.conf.
- You can edit the scripts to change paths or behavior as needed.

## Useful nmcli WiFi Commands

Here are some handy `nmcli` commands for managing WiFi networks on your Raspberry Pi:

- **List all known (saved) WiFi networks:**
  ```sh
  nmcli connection show
  ```

- **List available WiFi networks in range:**
  ```sh
  nmcli device wifi list
  ```

- **Show details for a specific connection:**
  ```sh
  nmcli connection show "<ConnectionName>"
  ```

- **Connect to a known WiFi network:**
  ```sh
  nmcli connection up "<ConnectionName>"
  ```

- **Disconnect from a WiFi network:**
  ```sh
  nmcli connection down "<ConnectionName>"
  ```

- **Delete a saved WiFi network:**
  ```sh
  nmcli connection delete "<ConnectionName>"
  ```

- **Rescan for WiFi networks:**
  ```sh
  nmcli device wifi rescan
  ```

- **Add a new WiFi network:**
  ```sh
  nmcli device wifi connect <SSID> password <password>
  ```
  Replace `<SSID>` with your WiFi network name and `<password>` with the WiFi password.

- **Change the priority of a WiFi network:**
  ```sh
  sudo nmcli connection modify "<ConnectionName>" connection.autoconnect-priority <number>
  ```
  A **higher number means higher priority**. Networks with a higher priority value will be preferred when connecting automatically.

Replace `<ConnectionName>` with the name of your WiFi connection as shown in the output of `nmcli connection show`. 


# Stopping the service for testing
```
# Stop the service (graceful shutdown)
sudo systemctl stop desktop-ai.service

# Check if it's stopped
sudo systemctl status desktop-ai.service
```
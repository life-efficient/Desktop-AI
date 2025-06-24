# Desktop-AI Auto-Start Setup

This project is designed to run automatically on Raspberry Pi startup. The scripts will ensure your code is always up-to-date, dependencies are installed, and your main Python application runs after every boot.

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
     - Add a `crontab` entry to run `start.sh` on every reboot

3. **Reboot to test:**
   ```sh
   sudo reboot
   ```

## What Happens on Boot?
- The `start.sh` script will:
  1. Pull the latest code from the `main` branch
  2. Create and activate a Python virtual environment at `~/venv` if it doesn't exist
  3. Install dependencies from `requirements.txt` (if present)
  4. Run `main.py` from your repo directory
  5. Log all actions to `startup.log` in the repo root

## Logs
- Setup actions: `setup.log`
- Startup actions and errors: `startup.log`

## Notes
- Make sure your `main.py` and `requirements.txt` are in the repo root as referenced in the scripts.
- You can edit the scripts to change paths or behavior as needed. 
#!/bin/bash

# Set 'preconfigured' connection to priority 20
sudo nmcli connection modify preconfigured connection.autoconnect-priority 20

echo "Enter WiFi SSID: "
read SSID
if [ -z "$SSID" ]; then
  echo "SSID cannot be empty. Exiting."
  exit 1
fi

echo "Enter WiFi Password: "
read -s PSK
echo
if [ -z "$PSK" ]; then
  echo "Password cannot be empty. Exiting."
  exit 1
fi

echo "Enter priority (optional, press Enter for default 10): "
read PRIORITY
if [ -z "$PRIORITY" ]; then
  PRIORITY=10
fi

# Check if connection profile already exists
PROFILE_EXISTS=$(sudo nmcli -t -f NAME connection show | grep -Fx "$SSID")

if [ -n "$PROFILE_EXISTS" ]; then
  echo "Updating existing connection profile for $SSID."
  sudo nmcli connection modify "$SSID" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PSK" connection.autoconnect-priority "$PRIORITY"
else
  echo "Adding new connection profile for $SSID."
  sudo nmcli connection add type wifi ifname wlan0 con-name "$SSID" ssid "$SSID"
  sudo nmcli connection modify "$SSID" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PSK" connection.autoconnect-priority "$PRIORITY"
fi

echo "Bringing up connection to $SSID..."
sudo nmcli connection up "$SSID"
echo "Done." 
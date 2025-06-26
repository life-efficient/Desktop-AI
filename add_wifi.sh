#!/bin/bash

CONF_FILE="/etc/wpa_supplicant/wpa_supplicant.conf"
BACKUP_FILE="/etc/wpa_supplicant/wpa_supplicant.conf.bak.$(date +%s)"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

read -p "Enter WiFi SSID: " SSID
if [ -z "$SSID" ]; then
  echo "SSID cannot be empty. Exiting."
  exit 1
fi

read -s -p "Enter WiFi Password: " PSK
echo
if [ -z "$PSK" ]; then
  echo "Password cannot be empty. Exiting."
  exit 1
fi

read -p "Enter priority (optional, press Enter to skip): " PRIORITY

# Backup the config file
cp "$CONF_FILE" "$BACKUP_FILE"
echo "Backup of config saved to $BACKUP_FILE"

# Build the network block
NETWORK_BLOCK="network={\n    ssid=\"$SSID\"\n    psk=\"$PSK\""
if [ -n "$PRIORITY" ]; then
  NETWORK_BLOCK+="\n    priority=$PRIORITY"
fi
NETWORK_BLOCK+="\n}"

# Append to the config file
echo -e "$NETWORK_BLOCK" >> "$CONF_FILE"
echo "Added WiFi network $SSID to $CONF_FILE" 
#!/bin/bash

# Test microphone recording and playback script
# Records for 5 seconds and plays back the recording

echo "Testing microphone recording and playback..."
echo "This will record for 5 seconds, then play it back."
echo ""

# Set output file
OUTPUT_FILE="test_recording.wav"

# Check if arecord is installed
if ! command -v arecord &> /dev/null; then
    echo "Error: arecord is not installed. Please install it first:"
    echo "  sudo apt-get install alsa-utils  # For Ubuntu/Debian"
    echo "  brew install alsa-lib             # For macOS"
    exit 1
fi

# Check if aplay is installed
if ! command -v aplay &> /dev/null; then
    echo "Error: aplay is not installed. Please install it first:"
    echo "  sudo apt-get install alsa-utils  # For Ubuntu/Debian"
    echo "  brew install alsa-lib             # For macOS"
    exit 1
fi

# Record audio for 5 seconds
echo "Recording for 5 seconds... (speak now)"
arecord -f S16_LE -r 44100 -c 1 -d 5 "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "Recording completed successfully!"
    echo ""
    
    # Play back the recording
    echo "Playing back the recording..."
    aplay "$OUTPUT_FILE"
    
    if [ $? -eq 0 ]; then
        echo "Playback completed!"
    else
        echo "Error: Failed to play back recording"
        exit 1
    fi
else
    echo "Error: Failed to record audio"
    exit 1
fi

# Clean up
echo ""
echo "Cleaning up test file..."
rm -f "$OUTPUT_FILE"
echo "Test completed!" 
#!/bin/bash

# Test speaker output using ALSA test files
# Plays various ALSA test sounds to verify speaker functionality

echo "Testing speaker output with ALSA test files..."
echo ""

# Check if aplay is installed
if ! command -v aplay &> /dev/null; then
    echo "Error: aplay is not installed. Please install it first:"
    echo "  sudo apt-get install alsa-utils  # For Ubuntu/Debian"
    echo "  brew install alsa-lib             # For macOS"
    exit 1
fi

# Check if ALSA test files are available
ALSA_TEST_DIR="/usr/share/sounds/alsa"
if [ ! -d "$ALSA_TEST_DIR" ]; then
    echo "Warning: ALSA test files not found in $ALSA_TEST_DIR"
    echo "Trying alternative locations..."
    
    # Try common alternative locations
    ALTERNATIVE_DIRS=(
        "/usr/share/alsa/sounds"
        "/usr/local/share/sounds/alsa"
        "/opt/homebrew/share/sounds/alsa"
    )
    
    for dir in "${ALTERNATIVE_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            ALSA_TEST_DIR="$dir"
            echo "Found ALSA test files in: $ALSA_TEST_DIR"
            break
        fi
    done
    
    if [ ! -d "$ALSA_TEST_DIR" ]; then
        echo "Error: ALSA test files not found. You may need to install them:"
        echo "  sudo apt-get install alsa-utils  # For Ubuntu/Debian"
        echo "  brew install alsa-lib             # For macOS"
        exit 1
    fi
fi

# List available test files
echo "Available test files in $ALSA_TEST_DIR:"
ls -la "$ALSA_TEST_DIR"/*.wav 2>/dev/null | head -10

echo ""
echo "Testing speaker with various ALSA test sounds..."

# Test files to play (in order of preference)
TEST_FILES=(
    "Front_Center.wav"
    "front-center.wav"
    "Front_Left.wav"
    "front-left.wav"
    "Front_Right.wav"
    "front-right.wav"
    "Center.wav"
    "center.wav"
    "Test.wav"
    "test.wav"
)

# Try to play each test file
for file in "${TEST_FILES[@]}"; do
    if [ -f "$ALSA_TEST_DIR/$file" ]; then
        echo "Playing: $file"
        aplay "$ALSA_TEST_DIR/$file"
        
        if [ $? -eq 0 ]; then
            echo "✓ Successfully played $file"
            echo ""
            
            # Ask user if they want to continue with more tests
            read -p "Press Enter to continue with next test, or 'q' to quit: " choice
            if [ "$choice" = "q" ]; then
                echo "Speaker test completed!"
                exit 0
            fi
        else
            echo "✗ Failed to play $file"
        fi
    fi
done

# If no standard test files found, try to play any .wav file
echo "No standard test files found. Trying any available .wav files..."
WAV_FILES=$(find "$ALSA_TEST_DIR" -name "*.wav" -type f | head -3)

if [ -n "$WAV_FILES" ]; then
    for file in $WAV_FILES; do
        filename=$(basename "$file")
        echo "Playing: $filename"
        aplay "$file"
        
        if [ $? -eq 0 ]; then
            echo "✓ Successfully played $filename"
            echo ""
            
            read -p "Press Enter to continue with next test, or 'q' to quit: " choice
            if [ "$choice" = "q" ]; then
                break
            fi
        else
            echo "✗ Failed to play $filename"
        fi
    done
else
    echo "No .wav files found in $ALSA_TEST_DIR"
    echo "You can manually test with: aplay /path/to/your/test.wav"
fi

echo "Speaker test completed!" 
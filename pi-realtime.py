#!/usr/bin/env python3
"""
Raspberry Pi Realtime Client with Audio Playback
This module provides a RealtimeClient with audio playback functionality for Raspberry Pi speakers.
"""

import os
import tempfile
import wave
import subprocess
import RPi.GPIO as GPIO
from realtime_client import RealtimeClient
from logging_util import get_logger

logger = get_logger(__name__)

# GPIO pin setup (reuse from main.py)
BUTTON_PIN = 17
LED_PIN = 27
SPEAKER_SHUTDOWN_PIN = 22
GPIO.setmode(GPIO.BCM)
GPIO.setup(SPEAKER_SHUTDOWN_PIN, GPIO.OUT)
GPIO.output(SPEAKER_SHUTDOWN_PIN, GPIO.LOW)  # Start with speaker disabled

# Speaker control

def enable_speaker():
    """Enable the speaker amplifier."""
    logger.info("Enabling speaker.")
    GPIO.output(SPEAKER_SHUTDOWN_PIN, GPIO.HIGH)

def disable_speaker():
    """Disable the speaker amplifier."""
    logger.info("Disabling speaker.")
    GPIO.output(SPEAKER_SHUTDOWN_PIN, GPIO.LOW)

# Audio playback function for PCM16 audio from RealtimeClient

def play_pcm16_audio(audio_data: bytes, sample_rate=24000):
    """
    Play PCM16 audio data through the Pi speaker using aplay.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            wav_path = f.name
            with wave.open(f, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)
        enable_speaker()
        subprocess.Popen([
            "aplay", "-D", "plughw:0,0", wav_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        disable_speaker()
    except Exception as e:
        logger.error(f"Error playing audio: {e}")
        disable_speaker()

# Main CLI loop

def main():
    print("Raspberry Pi Realtime Client with Audio")
    print("=" * 30)
    
    # Initialize RealtimeClient with audio playback
    try:
        client = RealtimeClient(
            audio_playback_func=play_pcm16_audio,
            input_modality="text",
            output_modality="audio"
        )
        print("✓ RealtimeClient initialized with text input and audio output")
    except Exception as e:
        print(f"✗ Failed to initialize RealtimeClient: {e}")
        GPIO.cleanup()
        return
    
    # Test WebSocket connection
    print("\n1. Testing WebSocket connection...")
    if client.connect_websocket():
        print("✓ WebSocket connection established")
        print(f"\nInteractive messaging mode (input: {client.input_modality}, output: {client.output_modality}):")
        print("  - Type your messages and press Enter to send")
        print("  - Type 'quit' or 'exit' to stop")
        print("  - Press Ctrl+C to stop the WebSocket connection")
        print("  - Audio responses will be played automatically")
        print("-" * 50)
        
        import threading
        import time
        
        def run_websocket():
            client.run_websocket()
        
        ws_thread = threading.Thread(target=run_websocket, daemon=True)
        ws_thread.start()
        time.sleep(1)
        
        # Text input loop
        try:
            while True:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Ending conversation...")
                    break
                if not user_input:
                    continue
                if client.send_text_message(user_input):
                    print("✓ Message sent")
                else:
                    print("✗ Failed to send message")
        except KeyboardInterrupt:
            print("\nInterrupted by user. Ending conversation...")
        except EOFError:
            print("\nEnd of input. Ending conversation...")
        finally:
            print("\nClosing WebSocket connection...")
            client.close_websocket()
            disable_speaker()
            GPIO.cleanup()
    else:
        print("✗ Failed to establish WebSocket connection")
        GPIO.cleanup()
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    main()
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
import sounddevice as sd
import numpy as np
import threading
import time
import sys

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

def normalize_audio(audio_array: np.ndarray) -> np.ndarray:
    """
    Normalize a numpy int16 array so the loudest sample is at full scale (32767).
    """
    max_val = np.max(np.abs(audio_array))
    if max_val == 0:
        return audio_array
    return (audio_array * (32767.0 / max_val)).astype(np.int16)

def play_pcm16_audio(audio_data: bytes, sample_rate=24000):
    """
    Play PCM16 audio data through the Pi speaker using aplay, and disable the speaker after playback.
    """
    def playback_thread():
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                wav_path = f.name
                with wave.open(f, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data)
            enable_speaker()
            proc = subprocess.Popen(
                ["aplay", "-D", "plughw:0,0", wav_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            proc.wait()  # Wait for playback to finish
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
        finally:
            disable_speaker()
    threading.Thread(target=playback_thread, daemon=True).start()

def record_and_stream(client):
    def callback(indata, frames, t, status):
        chunk = indata.astype(np.int16).tobytes()
        client.append_audio_buffer(chunk)
    stream = sd.InputStream(
        samplerate=24000, channels=1, dtype='int16', callback=callback, blocksize=1024
    )
    stream.start()
    return stream

# Main CLI loop

def main():
    # Parse command-line arguments for input/output modalities
    input_modality = 'audio'
    output_modality = 'audio'
    if len(sys.argv) > 1:
        input_modality = sys.argv[1].lower()
    if len(sys.argv) > 2:
        output_modality = sys.argv[2].lower()
    print(f"Input modality: {input_modality}")
    print(f"Output modality: {output_modality}")
    
    # Initialize RealtimeClient with audio playback
    try:
        client = RealtimeClient(
            audio_playback_func=play_pcm16_audio,
            input_modality=input_modality,
            output_modality=output_modality
        )
        print(f"✓ RealtimeClient initialized with input: {input_modality}, output: {output_modality}")
    except Exception as e:
        print(f"✗ Failed to initialize RealtimeClient: {e}")
        GPIO.cleanup()
        return
    
    # Test WebSocket connection
    print("\n1. Testing WebSocket connection...")
    if client.connect_websocket():
        print("✓ WebSocket connection established")
        if input_modality == 'audio':
            print("\nPush-to-Talk mode (button):")
            print("  - Hold button to talk (streaming)")
            print("  - Release button to send (must hold >0.5s)")
            print("  - Ctrl+C to exit")
            # (Assume BUTTON_PIN, LED_PIN, SPEAKER_SHUTDOWN_PIN, led, etc. are set up)
            # (Assume LED_PATTERN is defined)
            # (Assume led is initialized)
            stream = None
            button_was_down = False
            t0 = None
            try:
                while True:
                    button_is_down = GPIO.input(BUTTON_PIN) == GPIO.LOW
                    if button_is_down and not button_was_down:
                        # Button just pressed
                        client.clear_audio_buffer()
                        stream = record_and_stream(client)
                        # (Assume led.start(LED_PATTERN) is called)
                        t0 = time.time()
                    elif not button_is_down and button_was_down:
                        # Button just released
                        if stream:
                            stream.stop()
                            stream.close()
                            stream = None
                        # (Assume led.stop() is called)
                        held_time = time.time() - t0 if t0 else 0
                        if held_time > 0.5:
                            client.commit_audio_buffer()
                            client.create_response()
                            print("✓ Sent audio input and requested response.")
                        else:
                            print("Button press too short, ignoring.")
                    button_was_down = button_is_down
                    time.sleep(0.01)
            except KeyboardInterrupt:
                print("\nInterrupted by user. Ending conversation...")
            finally:
                print("\nClosing WebSocket connection...")
                client.close_websocket()
                GPIO.cleanup()
        else:
            print("\nText input mode:")
            print("  - Type your message and press Enter to send")
            print("  - Type 'quit' or 'exit' to stop")
            print("  - Ctrl+C to exit")
            import threading
            def run_websocket():
                client.run_websocket()
            ws_thread = threading.Thread(target=run_websocket, daemon=True)
            ws_thread.start()
            time.sleep(1)
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
            finally:
                print("\nClosing WebSocket connection...")
                client.close_websocket()
                GPIO.cleanup()
    else:
        print("✗ Failed to establish WebSocket connection")
        GPIO.cleanup()
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    main()
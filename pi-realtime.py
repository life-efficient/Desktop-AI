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
from hardware import Hardware

# LEDPatternController copied from main.py
class LEDPatternController:
    """Controls LED patterns using PWM"""
    PATTERNS = {
        "solid": "Steady brightness",
        "blink": "On/off blinking",
        "pulse": "Smooth breathing effect"
    }
    def __init__(self, pin, pwm_freq=100):
        self.pin = pin
        self.pwm_freq = pwm_freq
        self.pwm = None
        self.pattern = "solid"
        self.running = False
        self.thread = None
    def _setup_pwm(self):
        if self.pwm is None:
            self.pwm = GPIO.PWM(self.pin, self.pwm_freq)
            self.pwm.start(0)
    def _pattern_loop(self):
        self._setup_pwm()
        try:
            while self.running:
                if self.pattern == "solid":
                    self.pwm.ChangeDutyCycle(100)
                    time.sleep(0.1)
                elif self.pattern == "blink":
                    self.pwm.ChangeDutyCycle(100)
                    time.sleep(0.5)
                    if not self.running:
                        break
                    self.pwm.ChangeDutyCycle(0)
                    time.sleep(0.5)
                elif self.pattern == "pulse":
                    for dc in range(0, 101, 2):
                        if not self.running:
                            break
                        self.pwm.ChangeDutyCycle(dc)
                        time.sleep(0.01)
                    for dc in range(100, -1, -2):
                        if not self.running:
                            break
                        self.pwm.ChangeDutyCycle(dc)
                        time.sleep(0.01)
        finally:
            self.pwm.ChangeDutyCycle(0)
    def start(self, pattern=None):
        if pattern is not None:
            if pattern not in self.PATTERNS:
                raise ValueError(f"Invalid pattern. Choose from: {', '.join(self.PATTERNS.keys())}")
            self.pattern = pattern
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self._pattern_loop)
            self.thread.daemon = True
            self.thread.start()
    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
        GPIO.output(self.pin, GPIO.LOW)
    def cleanup(self):
        self.stop()
        if self.pwm is not None:
            self.pwm.stop()
            self.pwm = None
    @property
    def available_patterns(self):
        return self.PATTERNS

logger = get_logger(__name__)

# GPIO pin setup (reuse from main.py)
BUTTON_PIN = 17
LED_PIN = 27
SPEAKER_SHUTDOWN_PIN = 22
GPIO.setmode(GPIO.BCM)
GPIO.setup(SPEAKER_SHUTDOWN_PIN, GPIO.OUT)
GPIO.output(SPEAKER_SHUTDOWN_PIN, GPIO.LOW)  # Start with speaker disabled
GPIO.setup(LED_PIN, GPIO.OUT)

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

def play_pcm16_audio(audio_data: bytes, sample_rate=24000, hardware=None):
    """
    Play PCM16 audio data through the Pi speaker using aplay, and disable the speaker after playback.
    """
    def playback_thread():
        import tempfile, wave, subprocess
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                wav_path = f.name
                with wave.open(f, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data)
            hardware.enable_speaker()
            proc = subprocess.Popen(
                ["aplay", "-D", "plughw:0,0", wav_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            proc.wait()
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            hardware.disable_speaker()
    import threading
    threading.Thread(target=playback_thread, daemon=True).start()

def record_and_stream(client):
    def callback(indata, frames, t, status):
        chunk = indata.astype(np.int16).tobytes()
        if hasattr(client, 'is_connected') and client.is_connected:
            logger.info(f"Sending audio chunk of {len(chunk)} bytes to buffer.")
            client.append_audio_buffer(chunk)
        else:
            logger.warning("Tried to send audio chunk but client is not connected.")
    stream = sd.InputStream(
        samplerate=24000, channels=1, dtype='int16', callback=callback, blocksize=1024
    )
    stream.start()
    logger.info("Audio stream started.")
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
    print('yo')
    
    hardware = Hardware()
    # Initialize RealtimeClient with audio playback
    try:
        client = RealtimeClient(
            audio_playback_func=lambda audio, sr=24000: play_pcm16_audio(audio, sr, hardware),
            input_modality=input_modality,
            output_modality=output_modality
        )
        print(f"✓ RealtimeClient initialized with input: {input_modality}, output: {output_modality}")
    except Exception as e:
        print(f"✗ Failed to initialize RealtimeClient: {e}")
        hardware.cleanup()
        return
    
    led = LEDPatternController(LED_PIN)
    LED_PATTERN = "pulse"

    # No need to call connect_websocket() or start(); client is ready
    print("\n1. Testing WebSocket connection...")
    if client.is_connected:
        print("✓ WebSocket connection established")
        if input_modality == 'audio':
            print("\nPush-to-Talk mode (button):")
            print("  - Hold button to talk (streaming)")
            print("  - Release button to send (must hold >0.5s)")
            print("  - Ctrl+C to exit")
            stream = None
            button_was_down = False
            t0 = None
            try:
                while True:
                    button_is_down = hardware.button_pressed()
                    if button_is_down and not button_was_down:
                        logger.info("Button pressed. Starting audio stream and clearing buffer.")
                        client.clear_audio_buffer()
                        stream = record_and_stream(client)
                        hardware.led_on()
                        t0 = time.time()
                    elif not button_is_down and button_was_down:
                        logger.info("Button released. Stopping audio stream.")
                        if stream:
                            logger.info("Stopping and closing audio stream.")
                            stream.stop()
                            stream.close()
                            stream = None
                        hardware.led_off()
                        held_time = time.time() - t0 if t0 else 0
                        if held_time > 0.5:
                            logger.info("Committing audio buffer and requesting response.")
                            client.commit_audio_buffer()
                            client.create_response()
                            print("✓ Sent audio input and requested response.")
                        else:
                            logger.info("Button press too short, ignoring.")
                            print("Button press too short, ignoring.")
                    button_was_down = button_is_down
                    time.sleep(0.01)
            except KeyboardInterrupt:
                print("\nInterrupted by user. Ending conversation...")
            finally:
                logger.info("Main loop exiting. Cleaning up audio stream and websocket.")
                if stream:
                    logger.info("Stopping and closing audio stream in finally block.")
                    stream.stop()
                    stream.close()
                print("\nClosing WebSocket connection...")
                client.cleanup()
                hardware.cleanup()
        else:
            print("\nText input mode:")
            print("  - Type your message and press Enter to send")
            print("  - Type 'quit' or 'exit' to stop")
            print("  - Ctrl+C to exit")
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
                client.cleanup()
                hardware.cleanup()
    else:
        print("✗ Failed to establish WebSocket connection")
        hardware.cleanup()
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    main()
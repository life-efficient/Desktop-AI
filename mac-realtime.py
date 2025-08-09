#!/usr/bin/env python3
"""
macOS Realtime Client with Audio Playback
This module provides a RealtimeClient with audio playback functionality for macOS.
"""

import os
import io
import wave
import pyaudio
import threading
import queue
from realtime_client import RealtimeClient
from logging_util import get_logger
import sounddevice as sd
import numpy as np
import time
from pynput import keyboard  # pip install pynput
import sys

logger = get_logger(__name__)

class MacAudioPlayer:
    """
    Audio player for macOS using PyAudio.
    """
    
    def __init__(self):
        """
        Initialize the audio player.
        """
        self.pyaudio = pyaudio.PyAudio()
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.audio_thread = None
        
        # Audio settings for OpenAI's PCM16 format
        self.sample_rate = 24000  # OpenAI's default sample rate
        self.channels = 1  # Mono
        self.format = pyaudio.paInt16  # 16-bit PCM
        
        logger.info("MacAudioPlayer initialized")
    
    def play_audio(self, audio_data: bytes):
        """
        Play audio data.
        
        Args:
            audio_data: Raw PCM16 audio data
        """
        try:
            # Create a wave file in memory
            with io.BytesIO() as wav_buffer:
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(self.pyaudio.get_sample_size(self.format))
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_data)
                
                wav_buffer.seek(0)
                wav_data = wav_buffer.read()
            
            # Add to queue for playback
            self.audio_queue.put(wav_data)
            
            # Start playback thread if not already running
            if not self.is_playing:
                self._start_playback_thread()
                
        except Exception as e:
            logger.error(f"Failed to prepare audio for playback: {e}")
    
    def _start_playback_thread(self):
        """
        Start the audio playback thread.
        """
        if self.audio_thread and self.audio_thread.is_alive():
            return
        
        self.is_playing = True
        self.audio_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.audio_thread.start()
        logger.info("Audio playback thread started")
    
    def _playback_worker(self):
        """
        Worker thread for audio playback.
        """
        while self.is_playing:
            try:
                # Get audio data from queue (blocking)
                wav_data = self.audio_queue.get(timeout=1)
                
                # Play the audio
                with io.BytesIO(wav_data) as wav_buffer:
                    with wave.open(wav_buffer, 'rb') as wav_file:
                        # Open stream
                        stream = self.pyaudio.open(
                            format=self.pyaudio.get_format_from_width(wav_file.getsampwidth()),
                            channels=wav_file.getnchannels(),
                            rate=wav_file.getframerate(),
                            output=True
                        )
                        
                        # Read and play audio data
                        data = wav_file.readframes(1024)
                        while data:
                            stream.write(data)
                            data = wav_file.readframes(1024)
                        
                        # Clean up stream
                        stream.stop_stream()
                        stream.close()
                
                self.audio_queue.task_done()
                
            except queue.Empty:
                # No audio data in queue, check if we should continue
                if self.audio_queue.empty():
                    continue
            except Exception as e:
                logger.error(f"Error in audio playback: {e}")
                break
        
        logger.info("Audio playback thread stopped")
    
    def stop(self):
        """
        Stop audio playback and clean up.
        """
        self.is_playing = False
        if self.audio_thread:
            self.audio_thread.join(timeout=1)
        
        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break
        
        logger.info("Audio player stopped")
    
    def __del__(self):
        """
        Cleanup when object is destroyed.
        """
        self.stop()
        if hasattr(self, 'pyaudio'):
            self.pyaudio.terminate()


def create_audio_playback_function():
    """
    Create and return an audio playback function for the RealtimeClient.
    
    Returns:
        function: Audio playback function that accepts bytes
    """
    audio_player = MacAudioPlayer()
    
    def play_audio(audio_data: bytes):
        """
        Play audio data using the MacAudioPlayer.
        
        Args:
            audio_data: Raw PCM16 audio data
        """
        audio_player.play_audio(audio_data)
    
    return play_audio, audio_player


class PushToTalk:
    def __init__(self, client):
        self.client = client
        self.recording = False
        self.stream = None
        self.t0 = None
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.space_held = False

    def on_press(self, key):
        if key == keyboard.Key.space and not self.space_held:
            self.space_held = True
            print("Recording...")
            self.client.clear_audio_buffer()  # Clear buffer before new input
            self.recording = True
            self.stream, self.t0 = self.record_and_stream()

    def on_release(self, key):
        if key == keyboard.Key.space and self.space_held:
            self.space_held = False
            if self.stream:
                self.stream.stop()
                self.stream.close()
            held_time = time.time() - self.t0 if self.t0 else 0
            self.recording = False
            if held_time > 0.5:
                self.client.commit_audio_buffer()
                self.client.create_response()
                print("✓ Sent audio input and requested response.")
            else:
                print("Press was too short, ignoring.")

    def record_and_stream(self):
        def callback(indata, frames, t, status):
            chunk = indata.astype(np.int16).tobytes()
            self.client.append_audio_buffer(chunk)
        stream = sd.InputStream(
            samplerate=24000, channels=1, dtype='int16', callback=callback, blocksize=1024
        )
        stream.start()
        return stream, time.time()

    def run(self):
        self.listener.start()
        self.listener.join()

def main():
    print("macOS Realtime Client with Audio (Push-to-Talk or Text Input)")
    print("=" * 30)
    
    # Parse command-line arguments for input/output modalities
    input_modality = 'audio'
    output_modality = 'audio'
    if len(sys.argv) > 1:
        input_modality = sys.argv[1].lower()
    if len(sys.argv) > 2:
        output_modality = sys.argv[2].lower()
    print(f"Input modality: {input_modality}")
    print(f"Output modality: {output_modality}")
    
    # Create audio playback function
    audio_playback_func, audio_player = create_audio_playback_function()
    
    try:
        client = RealtimeClient(
            audio_playback_func=audio_playback_func,
            input_modality=input_modality,
            output_modality=output_modality
        )
        print(f"✓ RealtimeClient initialized with input: {input_modality}, output: {output_modality}")
    except Exception as e:
        print(f"✗ Failed to initialize RealtimeClient: {e}")
        return
    
    print("\n1. Testing WebSocket connection...")
    if client.connect_websocket():
        print("✓ WebSocket connection established")
        if input_modality == 'audio':
            print("\nPush-to-Talk mode:")
            print("  - Hold SPACEBAR to talk (streaming)")
            print("  - Release SPACEBAR to send (must hold >0.5s)")
            print("  - Press Ctrl+C to exit")
            print("-" * 50)
            import threading
            def run_websocket():
                client.run_websocket()
            ws_thread = threading.Thread(target=run_websocket, daemon=True)
            ws_thread.start()
            time.sleep(1)
            try:
                ptt = PushToTalk(client)
                ptt.run()
            except KeyboardInterrupt:
                print("\nInterrupted by user. Ending conversation...")
            except EOFError:
                print("\nEnd of input. Ending conversation...")
            finally:
                print("\nClosing WebSocket connection...")
                client.close_websocket()
                audio_player.stop()
        else:
            print("\nText input mode:")
            print("  - Type your message and press Enter to send")
            print("  - Type 'quit' or 'exit' to stop")
            print("  - Press Ctrl+C to exit")
            print("-" * 50)
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
            except EOFError:
                print("\nEnd of input. Ending conversation...")
            finally:
                print("\nClosing WebSocket connection...")
                client.close_websocket()
                audio_player.stop()
    else:
        print("✗ Failed to establish WebSocket connection")
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    main() 
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


def main():
    """
    Main function for macOS Realtime Client with audio.
    """
    print("macOS Realtime Client with Audio")
    print("=" * 30)
    
    # Create audio playback function
    audio_playback_func, audio_player = create_audio_playback_function()
    
    try:
        # Initialize client with text input and audio output
        client = RealtimeClient(
            audio_playback_func=audio_playback_func,
            input_modality="text",
            output_modality="audio"
        )
        print("✓ RealtimeClient initialized with text input and audio output")
    except Exception as e:
        print(f"✗ Failed to initialize RealtimeClient: {e}")
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
        
        # Start WebSocket in a separate thread
        import threading
        import time
        
        def run_websocket():
            client.run_websocket()
        
        # Start WebSocket thread
        ws_thread = threading.Thread(target=run_websocket, daemon=True)
        ws_thread.start()
        
        # Give WebSocket time to connect
        time.sleep(1)
        
        # Text input loop
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Ending conversation...")
                    break
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Send the text message (will trigger audio responses)
                if client.send_text_message(user_input):
                    print("✓ Message sent")
                else:
                    print("✗ Failed to send message")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Ending conversation...")
                break
            except EOFError:
                print("\n\nEnd of input. Ending conversation...")
                break
            except Exception as e:
                print(f"\nError: {e}")
                continue
        
        # Clean up
        print("\nClosing WebSocket connection...")
        client.close_websocket()
        audio_player.stop()
        
    else:
        print("✗ Failed to establish WebSocket connection")
    
    print("\n✓ All tests completed!")


if __name__ == "__main__":
    main() 
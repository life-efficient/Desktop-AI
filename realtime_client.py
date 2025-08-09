#!/usr/bin/env python3
"""
OpenAI Realtime API Client
This module provides a client for OpenAI's Realtime API using websockets.
"""

import os
import json
import websocket
from typing import Optional, Callable, Literal
from dotenv import load_dotenv
from logging_util import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# Type aliases for modalities
ModalityType = Literal["text", "audio"]

class RealtimeClient:
    """
    Client for OpenAI's Realtime API using websockets.
    
    This client supports both text and audio modalities:
    - Input modalities: "text" or "audio"
    - Output modalities: "text" or "audio" (audio always includes text as well)
    
    Note: When output_modality is "audio", both text and audio responses are requested
    from OpenAI, but only audio is played if audio_playback_func is provided.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 audio_playback_func: Optional[Callable] = None,
                 input_modality: ModalityType = "text",
                 output_modality: ModalityType = "text"):
        """
        Initialize the RealtimeClient.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY from .env)
            audio_playback_func: Optional function for playing audio (should accept bytes)
            input_modality: Input modality - "text" or "audio" (default: "text")
            output_modality: Output modality - "text" or "audio" (default: "text")
                          Note: "audio" will request both text and audio from OpenAI
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or .env file")
        
        # Validate modalities
        if input_modality not in ["text", "audio"]:
            raise ValueError("input_modality must be 'text' or 'audio'")
        if output_modality not in ["text", "audio"]:
            raise ValueError("output_modality must be 'text' or 'audio'")
        
        self.input_modality = input_modality
        self.output_modality = output_modality
        self.ws = None
        self.audio_playback_func = audio_playback_func
        self.audio_buffer = bytearray()
        
        # Validate audio playback function is provided when output_modality is audio
        if output_modality == "audio" and not audio_playback_func:
            logger.warning("output_modality is 'audio' but no audio_playback_func provided")
        
        logger.info(f"RealtimeClient initialized with input_modality={input_modality}, output_modality={output_modality}")
    
    def handle_event(self, data: dict):
        """
        Handle specific types of events with if/else blocks.
        
        Args:
            data: The event data received from the WebSocket
        """
        print(f"Handling event: {data}")
        event_type = data.get("type")
        
        if event_type == "response.done":
            response = data.get("response", {})
            output = response.get("output", [])
            
            # Extract AI response text from the output (always show text if available)
            for item in output:
                if item.get("type") == "message" and item.get("role") == "assistant":
                    content = item.get("content", [])
                    for content_item in content:
                        if content_item.get("type") == "text":
                            ai_response = content_item.get("text", "")
                            if ai_response:
                                print(f"\nAI: {ai_response}\n")
                                logger.info(f"AI Response: {ai_response}")
                            break
            
            # Play accumulated audio if available and output_modality is audio
            if self.output_modality == "audio" and self.audio_buffer and self.audio_playback_func:
                try:
                    self.audio_playback_func(bytes(self.audio_buffer))
                    logger.info(f"Played {len(self.audio_buffer)} bytes of audio")
                except Exception as e:
                    logger.error(f"Failed to play audio: {e}")
                finally:
                    self.audio_buffer.clear()
        
        elif event_type == "response.audio.delta":
            # Handle audio delta events - accumulate audio data (if output_modality includes audio)
            if self.output_modality == "audio":
                audio_data = data["delta"]
                if audio_data:
                    try:
                        # Decode base64 audio data and add to buffer
                        import base64
                        decoded_audio = base64.b64decode(audio_data)
                        self.audio_buffer.extend(decoded_audio)
                        logger.debug(f"Added {len(decoded_audio)} bytes to audio buffer")
                    except Exception as e:
                        logger.error(f"Failed to decode audio data: {e}")
        
        elif event_type == "conversation.item.create":
            item = data.get("item", {})
            if item.get("type") == "message" and item.get("role") == "user":
                content = item.get("content", [])
                for content_item in content:
                    if content_item.get("type") == "input_text":
                        user_text = content_item.get("text", "")
                        if user_text:
                            logger.info(f"User message received: {user_text}")
        
        elif event_type == "response.create":
            response = data.get("response", {})
            modalities = response.get("modalities", [])
            logger.info(f"Response creation triggered with modalities: {modalities}")
        
        elif event_type == "error":
            error = data.get("error", {})
            error_message = error.get("message", "Unknown error")
            logger.error(f"Error event received: {error_message}")
        
        else:
            # Dump the entire event for unknown types
            logger.info(f"Unknown event type '{event_type}': {json.dumps(data, indent=2)}")

    def connect_websocket(self, model: str = "gpt-4o-realtime-preview-2024-12-17", on_message: Optional[Callable] = None, on_open: Optional[Callable] = None):
        """
        Connect to the realtime WebSocket for listening to events.
        
        Args:
            model: Model to use for the WebSocket connection
            on_message: Optional callback function for handling messages
            on_open: Optional callback function for handling connection open
        """
        if not self.api_key:
            logger.error("No API key available")
            return False
        
        url = f"wss://api.openai.com/v1/realtime?model={model}"
        headers = [
            f"Authorization: Bearer {self.api_key}",
            "OpenAI-Beta: realtime=v1"
        ]
        
        def default_on_open(ws):
            logger.info("Connected to OpenAI Realtime WebSocket server.")
            if on_open:
                on_open(ws)
        
        def default_on_message(ws, message):
            try:
                data = json.loads(message)
                # Use the handle_event method to process the event
                self.handle_event(data)
                if on_message:
                    on_message(ws, data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message: {e}")
        
        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket connection closed.")
        
        self.ws = websocket.WebSocketApp(
            url,
            header=headers,
            on_open=default_on_open,
            on_message=default_on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        logger.info(f"WebSocket connection established to {url}")
        return True
    
    def send_text_message(self, text: str) -> bool:
        """
        Send a text message through the WebSocket connection.
        
        Args:
            text: The text message to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.ws:
            logger.error("No WebSocket connection. Call connect_websocket() first.")
            return False
        
        if self.input_modality != "text":
            logger.error(f"Cannot send text message when input_modality is '{self.input_modality}'")
            return False
        
        try:
            event = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": text,
                        }
                    ]
                }
            }
            
            message = json.dumps(event)
            self.ws.send(message)
            logger.info(f"Sent text message: {text}")
            
            # Trigger response creation with appropriate modalities
            self.create_response()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send text message: {e}")
            return False
    
    def send_audio_message(self, audio_data: bytes) -> bool:
        """
        Send an audio message through the WebSocket connection.
        
        Args:
            audio_data: Raw audio data to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.ws:
            logger.error("No WebSocket connection. Call connect_websocket() first.")
            return False
        
        if self.input_modality != "audio":
            logger.error(f"Cannot send audio message when input_modality is '{self.input_modality}'")
            return False
        
        try:
            # Encode audio data as base64
            import base64
            encoded_audio = base64.b64encode(audio_data).decode('utf-8')
            
            event = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "audio": encoded_audio,
                        }
                    ]
                }
            }
            
            message = json.dumps(event)
            self.ws.send(message)
            logger.info(f"Sent audio message: {len(audio_data)} bytes")
            
            # Trigger response creation with appropriate modalities
            self.create_response()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send audio message: {e}")
            return False
    
    def create_response(self, modalities: Optional[list] = None) -> bool:
        """
        Trigger a response creation from the model.
        
        Args:
            modalities: List of modalities for the response. If None, uses output_modality:
                       - "text": requests ["text"]
                       - "audio": requests ["text", "audio"] (text is always included)
            
        Returns:
            bool: True if response creation triggered successfully, False otherwise
        """
        if not self.ws:
            logger.error("No WebSocket connection. Call connect_websocket() first.")
            return False
        
        # Always include text modality, optionally add audio
        if modalities is None:
            if self.output_modality == "audio":
                modalities = ["text", "audio"]
            else:
                modalities = ["text"]
        
        try:
            event = {
                "type": "response.create",
                "response": {
                    "modalities": modalities
                }
            }
            
            message = json.dumps(event)
            self.ws.send(message)
            logger.info(f"Triggered response creation with modalities: {modalities}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to trigger response creation: {e}")
            return False
    
    def run_websocket(self):
        """
        Run the WebSocket connection in a blocking manner.
        """
        if not self.ws:
            logger.error("No WebSocket connection. Call connect_websocket() first.")
            return
        
        logger.info("Starting WebSocket connection...")
        self.ws.run_forever()
    
    def close_websocket(self):
        """
        Close the WebSocket connection.
        """
        if self.ws:
            self.ws.close()
            self.ws = None
            logger.info("WebSocket connection closed.")

    def append_audio_buffer(self, chunk: bytes, event_id: Optional[str] = None):
        """
        Append audio bytes to the input audio buffer (for streaming input to OpenAI).
        """
        if not self.ws:
            logger.error("No WebSocket connection. Call connect_websocket() first.")
            return False
        try:
            import base64
            encoded_audio = base64.b64encode(chunk).decode('utf-8')
            event = {
                "type": "input_audio_buffer.append",
                "audio": encoded_audio
            }
            if event_id:
                event["event_id"] = event_id
            self.ws.send(json.dumps(event))
            logger.debug(f"Appended {len(chunk)} bytes to audio buffer.")
            return True
        except Exception as e:
            logger.error(f"Failed to append audio buffer: {e}")
            return False

    def commit_audio_buffer(self, event_id: Optional[str] = None):
        """
        Commit the input audio buffer (finalize streaming input to OpenAI).
        """
        if not self.ws:
            logger.error("No WebSocket connection. Call connect_websocket() first.")
            return False
        try:
            event = {
                "type": "input_audio_buffer.commit"
            }
            if event_id:
                event["event_id"] = event_id
            self.ws.send(json.dumps(event))
            logger.info("Committed audio buffer.")
            return True
        except Exception as e:
            logger.error(f"Failed to commit audio buffer: {e}")
            return False

    def clear_audio_buffer(self, event_id: Optional[str] = None):
        """
        Clear the input audio buffer before starting a new user input (when VAD is disabled).
        """
        if not self.ws:
            logger.error("No WebSocket connection. Call connect_websocket() first.")
            return False
        try:
            event = {
                "type": "input_audio_buffer.clear"
            }
            if event_id:
                event["event_id"] = event_id
            self.ws.send(json.dumps(event))
            logger.info("Cleared audio buffer.")
            return True
        except Exception as e:
            logger.error(f"Failed to clear audio buffer: {e}")
            return False


def main():
    """
    Test the RealtimeClient WebSocket functionality.
    """
    print("Testing RealtimeClient WebSocket")
    print("=" * 30)
    
    # Initialize client with text input and text output
    try:
        client = RealtimeClient(input_modality="text", output_modality="text")
        print("✓ RealtimeClient initialized successfully with text input/output")
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
                
                # Send the text message
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
        
    else:
        print("✗ Failed to establish WebSocket connection")
    
    print("\n✓ All tests completed!")


if __name__ == "__main__":
    main() 
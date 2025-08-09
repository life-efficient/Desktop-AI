#!/usr/bin/env python3
"""
OpenAI Realtime API Client
This module provides a client for OpenAI's Realtime API using websockets.
"""

import os
import json
import websocket
from typing import Optional, Callable
from dotenv import load_dotenv
from logging_util import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

class RealtimeClient:
    """
    Client for OpenAI's Realtime API using websockets.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the RealtimeClient.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY from .env)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or .env file")
        
        self.ws = None
        
        logger.info("RealtimeClient initialized")
    
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
                logger.info(f"Received event: {json.dumps(data, indent=2)}")
                
                # Handle response.done events specifically
                if data.get("type") == "response.done":
                    response = data.get("response", {})
                    output = response.get("output", [])
                    
                    # Extract AI response text from the output
                    for item in output:
                        if item.get("type") == "message" and item.get("role") == "assistant":
                            content = item.get("content", [])
                            for content_item in content:
                                if content_item.get("type") == "text":
                                    ai_response = content_item.get("text", "")
                                    if ai_response:
                                        print(f"\n🤖 AI: {ai_response}\n")
                                        logger.info(f"AI Response: {ai_response}")
                                    break
                
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
            
            # Trigger response creation
            self.create_response()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send text message: {e}")
            return False
    
    def create_response(self, modalities: list = ["text"]) -> bool:
        """
        Trigger a response creation from the model.
        
        Args:
            modalities: List of modalities for the response (default: ["text"])
            
        Returns:
            bool: True if response creation triggered successfully, False otherwise
        """
        if not self.ws:
            logger.error("No WebSocket connection. Call connect_websocket() first.")
            return False
        
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


def main():
    """
    Test the RealtimeClient WebSocket functionality.
    """
    print("Testing RealtimeClient WebSocket")
    print("=" * 30)
    
    # Initialize client
    try:
        client = RealtimeClient()
        print("✓ RealtimeClient initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize RealtimeClient: {e}")
        return
    
    # Test WebSocket connection
    print("\n1. Testing WebSocket connection...")
    if client.connect_websocket():
        print("✓ WebSocket connection established")
        print("\nInteractive text messaging mode:")
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
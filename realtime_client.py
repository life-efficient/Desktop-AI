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
        print("  Press Ctrl+C to stop the WebSocket connection...")
        try:
            client.run_websocket()
        except KeyboardInterrupt:
            print("\nStopping WebSocket connection...")
            client.close_websocket()
    else:
        print("✗ Failed to establish WebSocket connection")
    
    print("\n✓ All tests completed!")


if __name__ == "__main__":
    main() 
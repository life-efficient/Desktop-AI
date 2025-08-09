#!/usr/bin/env python3
"""
Realtime API integration for OpenAI's Realtime API
This module provides a class to manage realtime sessions for instant audio responses.
"""

import os
import json
import time
import asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
from openai import OpenAI
from dotenv import load_dotenv
from logging_util import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

class RealtimeManager:
    """
    Manages OpenAI Realtime API sessions for instant audio responses.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the RealtimeManager.
        
        Args:
            model: The model to use for the realtime session (default: gpt-4o-mini)
        """
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        
        self.model = model
        self.session = None
        self.session_id = None
        self.is_connected = False
        
        # Default system message
        self.system_message = "You are a helpful assistant engaging in a voice conversation. Keep your responses clear and concise."
        
        logger.info(f"RealtimeManager initialized with model: {model}")
    
    def create_session(self, system_message: Optional[str] = None) -> bool:
        """
        Create a new realtime session.
        
        Args:
            system_message: Optional custom system message
            
        Returns:
            bool: True if session created successfully, False otherwise
        """
        try:
            # Prepare the system message
            if system_message:
                self.system_message = system_message
            
            # Create the session using the beta realtime API
            self.session = self.client.beta.realtime_sessions.create(
                model=self.model,
                system_message=self.system_message
            )
            
            self.session_id = self.session.id
            self.is_connected = True
            
            logger.info(f"Realtime session created successfully. Session ID: {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create realtime session: {e}")
            return False
    
    def get_response(self, message: str) -> Optional[str]:
        """
        Get a response from the realtime session.
        
        Args:
            message: The user's message
            
        Returns:
            str: The assistant's response, or None if failed
        """
        if not self.is_connected or not self.session:
            logger.error("No active session. Call create_session() first.")
            return None
        
        try:
            # Send the message to the session
            response = self.session.send_message(message)
            
            # Extract the response text
            if response and hasattr(response, 'content'):
                # Handle different response formats
                if isinstance(response.content, list):
                    # Extract text from content list
                    for item in response.content:
                        if hasattr(item, 'type') and item.type == 'text':
                            return item.text
                elif isinstance(response.content, str):
                    return response.content
                else:
                    # Try to get text from the response object
                    return str(response.content)
            
            logger.warning("No text content found in response")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get response: {e}")
            return None
    
    async def get_response_stream(self, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get a streaming response from the realtime session.
        
        Args:
            message: The user's message
            
        Yields:
            dict: Response chunks with type and data
        """
        if not self.is_connected or not self.session:
            logger.error("No active session. Call create_session() first.")
            return
        
        try:
            # Send the message and get streaming response
            async for chunk in self.session.send_message(message, stream=True):
                if chunk and hasattr(chunk, 'content'):
                    if isinstance(chunk.content, list):
                        for item in chunk.content:
                            if hasattr(item, 'type') and item.type == 'text':
                                yield {"type": "text", "data": item.text}
                    elif isinstance(chunk.content, str):
                        yield {"type": "text", "data": chunk.content}
                    else:
                        yield {"type": "text", "data": str(chunk.content)}
                elif chunk and hasattr(chunk, 'type'):
                    yield {"type": chunk.type, "data": chunk}
                        
        except Exception as e:
            logger.error(f"Failed to get streaming response: {e}")
            yield {"type": "error", "data": str(e)}
    
    def close_session(self) -> bool:
        """
        Close the current realtime session.
        
        Returns:
            bool: True if session closed successfully, False otherwise
        """
        if not self.session:
            logger.warning("No active session to close")
            return True
        
        try:
            self.session.close()
            self.session = None
            self.session_id = None
            self.is_connected = False
            
            logger.info("Realtime session closed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to close session: {e}")
            return False
    
    def is_session_active(self) -> bool:
        """
        Check if the session is currently active.
        
        Returns:
            bool: True if session is active, False otherwise
        """
        return self.is_connected and self.session is not None
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get information about the current session.
        
        Returns:
            dict: Session information
        """
        if not self.session:
            return {"status": "no_session"}
        
        return {
            "session_id": self.session_id,
            "model": self.model,
            "is_connected": self.is_connected,
            "status": "active"
        }


async def main_async():
    """
    Interactive async usage of the RealtimeManager class.
    """
    # Initialize the realtime manager
    realtime = RealtimeManager()
    
    # Create a session
    if realtime.create_session():
        print("Session created successfully! (Async Mode)")
        print("Type your messages and press Enter. Type 'quit' or 'exit' to end the conversation.")
        print("-" * 50)
        
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
                
                # Get streaming response from the realtime session
                print("Assistant: ", end="", flush=True)
                
                async for chunk in realtime.get_response_stream(user_input):
                    if chunk["type"] == "text":
                        print(chunk["data"], end="", flush=True)
                    elif chunk["type"] == "error":
                        print(f"\nError: {chunk['data']}")
                        break
                
                print()  # New line after response
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Ending conversation...")
                break
            except EOFError:
                print("\n\nEnd of input. Ending conversation...")
                break
            except Exception as e:
                print(f"\nError: {e}")
                continue
        
        # Close the session
        print("\nClosing session...")
        realtime.close_session()
        print("Session closed.")
    else:
        print("Failed to create session.")


def main():
    """
    Interactive usage of the RealtimeManager class (synchronous).
    """
    # Initialize the realtime manager
    realtime = RealtimeManager()
    
    # Create a session
    if realtime.create_session():
        print("Session created successfully!")
        print("Type your messages and press Enter. Type 'quit' or 'exit' to end the conversation.")
        print("-" * 50)
        
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
                
                # Get response from the realtime session
                print("Assistant: ", end="", flush=True)
                response = realtime.get_response(user_input)
                
                if response:
                    print(response)
                else:
                    print("Sorry, I couldn't generate a response.")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Ending conversation...")
                break
            except EOFError:
                print("\n\nEnd of input. Ending conversation...")
                break
            except Exception as e:
                print(f"\nError: {e}")
                continue
        
        # Close the session
        print("\nClosing session...")
        realtime.close_session()
        print("Session closed.")
    else:
        print("Failed to create session.")


if __name__ == "__main__":
    # Check if we should run async or sync version
    import sys
    if "--async" in sys.argv:
        asyncio.run(main_async())
    else:
        main() 
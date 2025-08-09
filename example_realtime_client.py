#!/usr/bin/env python3
"""
Example usage of the RealtimeClient class.
This script demonstrates how to use the RealtimeClient to create a session.
"""

from realtime_client import RealtimeClient
from logging_util import get_logger

logger = get_logger(__name__)

def example_session_creation():
    """Example of creating a realtime session."""
    print("RealtimeClient Example - Session Creation")
    print("=" * 40)
    
    # Initialize the client
    client = RealtimeClient()
    
    # Create a session
    print("Creating realtime session...")
    if client.create_session():
        print("✓ Session created successfully!")
        print(f"Session ID: {client.session.get('id') if client.session else 'None'}")
        print(f"Session data: {client.session}")
    else:
        print("✗ Failed to create session")
        return
    
    print("\nSession creation completed!")

if __name__ == "__main__":
    example_session_creation() 
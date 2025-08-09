#!/usr/bin/env python3
"""
Test script for the RealtimeClient class.
"""

from realtime_client import RealtimeClient
from logging_util import get_logger

logger = get_logger(__name__)

def test_realtime_client():
    """Test the RealtimeClient functionality."""
    print("Testing RealtimeClient")
    print("=" * 30)
    
    # Initialize client
    try:
        client = RealtimeClient()
        print("✓ RealtimeClient initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize RealtimeClient: {e}")
        return
    
    # Test session creation
    print("\n1. Testing session creation...")
    if client.create_session():
        print("✓ Session created successfully")
        print(f"  Session ID: {client.session.get('id') if client.session else 'None'}")
        print(f"  Session data: {client.session}")
    else:
        print("✗ Failed to create session")
        return
    
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    test_realtime_client() 
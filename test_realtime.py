#!/usr/bin/env python3
"""
Test script for the RealtimeManager class.
"""

import asyncio
from realtime import RealtimeManager
from logging_util import get_logger

logger = get_logger(__name__)

async def test_realtime_async():
    """Test the async functionality of RealtimeManager."""
    print("Testing RealtimeManager (Async Mode)")
    print("=" * 40)
    
    realtime = RealtimeManager()
    
    # Test session creation
    print("1. Creating session...")
    if realtime.create_session():
        print("✓ Session created successfully")
        
        # Test streaming response
        print("\n2. Testing streaming response...")
        test_message = "Hello! Can you tell me a short joke?"
        print(f"User: {test_message}")
        print("Assistant: ", end="", flush=True)
        
        async for chunk in realtime.get_response_stream(test_message):
            if chunk["type"] == "text":
                print(chunk["data"], end="", flush=True)
            elif chunk["type"] == "error":
                print(f"\n✗ Error: {chunk['data']}")
                break
        
        print("\n✓ Streaming response completed")
        
        # Test regular response
        print("\n3. Testing regular response...")
        test_message2 = "What's 2 + 2?"
        print(f"User: {test_message2}")
        response = realtime.get_response(test_message2)
        if response:
            print(f"Assistant: {response}")
            print("✓ Regular response completed")
        else:
            print("✗ Failed to get regular response")
        
        # Close session
        print("\n4. Closing session...")
        if realtime.close_session():
            print("✓ Session closed successfully")
        else:
            print("✗ Failed to close session")
            
    else:
        print("✗ Failed to create session")

def test_realtime_sync():
    """Test the synchronous functionality of RealtimeManager."""
    print("Testing RealtimeManager (Sync Mode)")
    print("=" * 40)
    
    realtime = RealtimeManager()
    
    # Test session creation
    print("1. Creating session...")
    if realtime.create_session():
        print("✓ Session created successfully")
        
        # Test regular response
        print("\n2. Testing regular response...")
        test_message = "Hello! How are you today?"
        print(f"User: {test_message}")
        response = realtime.get_response(test_message)
        if response:
            print(f"Assistant: {response}")
            print("✓ Regular response completed")
        else:
            print("✗ Failed to get regular response")
        
        # Close session
        print("\n3. Closing session...")
        if realtime.close_session():
            print("✓ Session closed successfully")
        else:
            print("✗ Failed to close session")
            
    else:
        print("✗ Failed to create session")

if __name__ == "__main__":
    import sys
    
    if "--async" in sys.argv:
        print("Running async test...")
        asyncio.run(test_realtime_async())
    else:
        print("Running sync test...")
        test_realtime_sync() 
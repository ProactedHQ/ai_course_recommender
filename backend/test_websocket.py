#!/usr/bin/env python
"""
WebSocket Connection Test Script
Tests WebSocket connectivity for recommendations and notifications channels.

Usage:
    python test_websocket.py
"""
import asyncio
import websockets
import json
import sys


async def test_recommendation_ws():
    """Test recommendation WebSocket endpoint"""
    uri = "ws://localhost:8000/ws/recommendations/"
    
    print(f"\n{'='*70}")
    print("Testing Recommendation WebSocket")
    print(f"{'='*70}")
    print(f"Connecting to: {uri}\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Wait for connection confirmation
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 Received: {json.dumps(data, indent=2)}")
            
            # Send a test message
            test_msg = {"type": "ping", "message": "Hello from test script"}
            await websocket.send(json.dumps(test_msg))
            print(f"\n📤 Sent: {json.dumps(test_msg, indent=2)}")
            
            # Wait for response
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 Received: {json.dumps(data, indent=2)}")
            
            print("\n✅ Recommendation WebSocket test PASSED!")
            return True
            
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_notification_ws():
    """Test notification WebSocket endpoint"""
    uri = "ws://localhost:8000/ws/notifications/"
    
    print(f"\n{'='*70}")
    print("Testing Notification WebSocket")
    print(f"{'='*70}")
    print(f"Connecting to: {uri}\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Wait for connection confirmation
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📨 Received: {json.dumps(data, indent=2)}")
            
            print("\n✅ Notification WebSocket test PASSED!")
            return True
            
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Run all WebSocket tests"""
    print("\n🧪 AI Course Recommender - WebSocket Connection Tests")
    print("="*70)
    print("⚠️  Make sure the server is running with WebSocket support!")
    print("    Run: python run_server.py")
    print("="*70)
    
    # Test recommendation WebSocket
    recommendation_ok = await test_recommendation_ws()
    
    # Test notification WebSocket
    notification_ok = await test_notification_ws()
    
    # Summary
    print(f"\n{'='*70}")
    print("Test Summary")
    print(f"{'='*70}")
    print(f"Recommendation WebSocket: {'✅ PASS' if recommendation_ok else '❌ FAIL'}")
    print(f"Notification WebSocket:   {'✅ PASS' if notification_ok else '❌ FAIL'}")
    print(f"{'='*70}\n")
    
    if recommendation_ok and notification_ok:
        print("🎉 All WebSocket tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check server logs for details.")
        print("\nTroubleshooting:")
        print("1. Ensure Redis is running: redis-cli ping")
        print("2. Check server is in ASGI mode (should see 'WebSocket support enabled')")
        print("3. Verify authentication (this test requires auth token)")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)

#!/usr/bin/env python3
"""
Test script to verify Upstox WebSocket token works
"""

import sys
import json
import upstox_client
import time

# Load Upstox config
with open('upstox_config.json', 'r') as f:
    config = json.load(f)

ACCESS_TOKEN = config['access_token']

def test_websocket_connection():
    """Test if WebSocket connection works with current token"""

    print("🔍 Testing Upstox WebSocket Token...")

    # Create WebSocket client
    configuration = upstox_client.Configuration()
    configuration.access_token = ACCESS_TOKEN

    try:
        streamer = upstox_client.MarketDataStreamerV3(
            upstox_client.ApiClient(configuration)
        )

        connected = False
        error_received = False

        def on_open():
            nonlocal connected
            connected = True
            print("✅ WebSocket connected successfully!")
            streamer.disconnect()

        def on_error(error):
            nonlocal error_received
            error_received = True
            print(f"❌ WebSocket error: {error}")

        def on_close(*args):
            print("🔌 WebSocket closed")

        # Register callbacks
        streamer.on("open", on_open)
        streamer.on("error", on_error)
        streamer.on("close", on_close)

        print("🚀 Attempting WebSocket connection...")
        streamer.connect()

        # Wait for connection result
        timeout = 10
        start_time = time.time()

        while not connected and not error_received and (time.time() - start_time) < timeout:
            time.sleep(0.5)

        if connected:
            print("🎉 SUCCESS: WebSocket token is valid!")
            return True
        elif error_received:
            print("💥 FAILED: WebSocket token rejected")
            return False
        else:
            print("⏰ TIMEOUT: No response from WebSocket")
            streamer.disconnect()
            return False

    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return False

def test_http_api():
    """Test if HTTP API works with current token"""

    print("\n🔍 Testing Upstox HTTP API...")

    configuration = upstox_client.Configuration()
    configuration.access_token = ACCESS_TOKEN

    try:
        api_client = upstox_client.ApiClient(configuration)
        api_instance = upstox_client.MarketQuoteApi(api_client)

        # Test with a simple stock
        instrument_key = "NSE_EQ|INE002A01018"  # RELIANCE
        api_version = "v3"

        result = api_instance.get_market_quote_ltp(instrument_key, api_version)
        print(f"✅ HTTP API works! LTP: {result.data.last_price}")

        return True

    except Exception as e:
        print(f"❌ HTTP API failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Upstox Token Validation Test\n")

    # Test HTTP API first
    http_works = test_http_api()

    # Test WebSocket
    ws_works = test_websocket_connection()

    print("\n📊 RESULTS:")
    print(f"   HTTP API: {'✅ Working' if http_works else '❌ Failed'}")
    print(f"   WebSocket: {'✅ Working' if ws_works else '❌ Failed'}")

    if http_works and not ws_works:
        print("\n🔍 DIAGNOSIS: Token works for HTTP but not WebSocket")
        print("   Possible causes:")
        print("   - Another application using WebSocket with same token")
        print("   - WebSocket rate limits")
        print("   - Token permissions issue")
    elif not http_works and not ws_works:
        print("\n🔍 DIAGNOSIS: Token is expired/invalid")
    else:
        print("\n🎉 SUCCESS: Token works for both HTTP and WebSocket!")

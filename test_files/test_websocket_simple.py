#!/usr/bin/env python3
"""
Minimal WebSocket Test Script
Tests basic WebSocket connection with single stock subscription
Based on option trading bot approach but using stock credentials
"""

import upstox_client
import json
import os
import sys
import logging
from datetime import datetime
import pytz

# Enhanced logging as suggested by expert
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('websocket').setLevel(logging.DEBUG)
logging.getLogger('upstox_client').setLevel(logging.DEBUG)

IST = pytz.timezone('Asia/Kolkata')

def load_config():
    """Load Upstox configuration"""
    config_file = "upstox_config.json"
    if not os.path.exists(config_file):
        print(f"❌ Config file not found: {config_file}")
        return None

    with open(config_file, 'r') as f:
        return json.load(f)

def test_single_stock_websocket():
    """Test WebSocket connection with single stock"""
    print("🔬 Minimal WebSocket Test - Single Stock")
    print("=" * 50)

    # Load config
    config = load_config()
    if not config:
        return False

    access_token = config.get('access_token')
    if not access_token:
        print("❌ No access token found")
        return False

    print(f"✅ Loaded access token (ends with: ...{access_token[-4:]})")

    # Pick a single stock - RELIANCE
    test_symbol = "RELIANCE"
    test_instrument_key = "NSE_EQ|INE002A01018"

    print(f"🎯 Testing with: {test_symbol} ({test_instrument_key})")

    try:
        # Setup configuration (stock credentials)
        configuration = upstox_client.Configuration()
        configuration.access_token = access_token

        # Create streamer
        streamer = upstox_client.MarketDataStreamerV3(
            upstox_client.ApiClient(configuration)
        )

        # Track connection state
        connected = False
        message_count = 0

        def on_open():
            nonlocal connected
            connected = True
            current_time = datetime.now(IST).strftime('%H:%M:%S')
            print(f"✅ WebSocket OPENED at {current_time}")

            # Subscribe to single stock
            try:
                streamer.subscribe([test_instrument_key], "full")
                print(f"📡 Subscribed to {test_symbol} at {datetime.now(IST).strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"❌ Subscription failed: {e}")

        def on_message(message):
            nonlocal message_count
            message_count += 1
            current_time = datetime.now(IST).strftime('%H:%M:%S')

            try:
                # Handle dict messages (SDK auto-decodes)
                if isinstance(message, dict) and 'feeds' in message:
                    feeds = message['feeds']
                    for instrument_key, feed_data in feeds.items():
                        if instrument_key == test_instrument_key:
                            # Extract LTP
                            ltp = None
                            if 'fullFeed' in feed_data:
                                full_feed = feed_data['fullFeed']
                                if 'marketFF' in full_feed:
                                    market_ff = full_feed['marketFF']
                                    if 'ltpc' in market_ff:
                                        ltpc_data = market_ff['ltpc']
                                        ltp = ltpc_data.get('ltp')

                            if ltp:
                                print(f"📊 {current_time} | {test_symbol}: ₹{float(ltp):.2f} (dict msg #{message_count})")
                            else:
                                print(f"📊 {current_time} | {test_symbol}: No LTP data (dict msg #{message_count})")

                # Handle binary protobuf messages (like option bot)
                elif isinstance(message, bytes):
                    try:
                        from MarketDataFeedV3_pb2 import FeedResponse
                        feed_response = FeedResponse()
                        feed_response.ParseFromString(message)

                        for instrument_key, feed_data in feed_response.feeds.items():
                            if instrument_key == test_instrument_key:
                                # Extract LTP from protobuf
                                ltp = None
                                if feed_data.HasField('fullFeed'):
                                    full_feed = feed_data.fullFeed
                                    if full_feed.HasField('marketFF'):
                                        market_ff = full_feed.marketFF
                                        if market_ff.HasField('ltpc'):
                                            ltpc = market_ff.ltpc
                                            ltp = float(ltpc.ltp)

                                if ltp:
                                    print(f"📊 {current_time} | {test_symbol}: ₹{ltp:.2f} (protobuf msg #{message_count})")
                                else:
                                    print(f"📊 {current_time} | {test_symbol}: No LTP data (protobuf msg #{message_count})")

                    except ImportError:
                        print(f"⚠️ Protobuf decoder not available for binary msg #{message_count}")
                    except Exception as e:
                        print(f"❌ Protobuf decode error: {e}")

                else:
                    print(f"📨 Received {type(message)} message (#{message_count})")

            except Exception as e:
                print(f"❌ Message processing error: {e}")

        def on_error(error):
            current_time = datetime.now(IST).strftime('%H:%M:%S')
            print(f"❌ WebSocket ERROR at {current_time}: {error}")

        def on_close(*args):
            nonlocal connected
            connected = False
            current_time = datetime.now(IST).strftime('%H:%M:%S')
            close_code = args[0] if args else "unknown"
            close_reason = args[1] if len(args) > 1 else "unknown"
            print(f"⚠️ WebSocket CLOSED at {current_time} - Code: {close_code}, Reason: {close_reason}")

        # Register callbacks
        streamer.on("open", on_open)
        streamer.on("message", on_message)
        streamer.on("error", on_error)
        streamer.on("close", on_close)

        # Connect with graceful error handling
        print(f"🔌 Connecting to Upstox WebSocket at {datetime.now(IST).strftime('%H:%M:%S')}...")

        try:
            streamer.connect()

            # Wait for connection and test
            import time
            start_time = time.time()
            max_wait = 30  # 30 seconds max

            print("⏳ Waiting for connection and first tick...")

            while time.time() - start_time < max_wait:
                time.sleep(1)

                if connected and message_count > 0:
                    print("✅ SUCCESS: WebSocket connected and receiving data!")
                    return True

                if not connected and time.time() - start_time > 10:
                    # If not connected after 10 seconds, likely failed
                    print("❌ FAILED: WebSocket not connected after 10 seconds")
                    break

            if message_count == 0:
                print("❌ FAILED: No data received - WebSocket subscription blocked")
                return False

            return True

        except KeyboardInterrupt:
            print("🛑 Test interrupted by user")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        finally:
            # GRACEFUL WEBSOCKET CLEANUP (prevents lingering connections)
            print("🧹 Performing graceful WebSocket cleanup...")
            try:
                streamer.disconnect()
                print("✅ WebSocket disconnected gracefully")
                time.sleep(2)  # Give server time to process disconnect
            except Exception as cleanup_err:
                print(f"⚠️ Cleanup warning: {cleanup_err}")

    except Exception as e:
        print(f"❌ Connection failed with error: {e}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Starting WebSocket Diagnostic Test")
    print("This will test basic WebSocket connection with single stock")
    print("Using stock app credentials (not option app)")
    print()

    success = test_single_stock_websocket()

    print()
    print("=" * 50)
    if success:
        print("🎉 TEST PASSED: WebSocket working correctly")
        print("The 403 error may be related to multiple stocks or specific stocks")
    else:
        print("💥 TEST FAILED: WebSocket connection blocked")
        print("Issue confirmed - contact Upstox support with logs above")
    print("=" * 50)

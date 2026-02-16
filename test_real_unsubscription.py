#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to simulate real unsubscription and verify ticks stop
Uses the exact same approach as run_continuation.py
"""

import sys
import os
from datetime import datetime
import time

# Add src to path
sys.path.insert(0, 'src')

def test_real_unsubscription():
    """Test that unsubscription actually stops ticks using continuation bot approach"""
    
    print("=== TESTING REAL UNSUBSCRIPTION BEHAVIOR ===")
    print("Using the exact same approach as run_continuation.py")
    print()
    
    try:
        # Import the exact same modules used in run_continuation.py
        from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer
        from src.utils.upstox_fetcher import UpstoxFetcher
        
        # Test with real stocks that should have data
        test_symbol = "ADANIPOWER"
        test_instrument_key = "NSE_EQ|INE049A01022"
        
        print(f"Testing with {test_symbol} ({test_instrument_key})")
        
        # STEP 1: SETUP - Create data streamer exactly like run_continuation.py
        print("=== STEP 1: SETUP (like run_continuation.py) ===")
        
        # Get instrument key using UpstoxFetcher (like run_continuation.py)
        upstox_fetcher = UpstoxFetcher()
        try:
            instrument_key = upstox_fetcher.get_instrument_key(test_symbol)
            if not instrument_key:
                print(f"❌ Could not get instrument key for {test_symbol}")
                return False
            print(f"✅ Got instrument key: {instrument_key}")
        except Exception as e:
            print(f"❌ Error getting instrument key: {e}")
            return False
        
        # Create SimpleStockStreamer exactly like run_continuation.py
        instrument_keys = [instrument_key]
        stock_symbols = {instrument_key: test_symbol}
        
        print(f"Creating SimpleStockStreamer with {len(instrument_keys)} stocks")
        data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)
        
        # STEP 2: SUBSCRIBE - Connect and subscribe exactly like run_continuation.py
        print("\n=== STEP 2: SUBSCRIBE AND RECEIVE TICKS ===")
        
        # Connect to data stream exactly like run_continuation.py
        print("Connecting to data stream...")
        if not data_streamer.connect():
            print("❌ FAILED to connect to data stream")
            return False
        
        print("✅ Connected! Waiting for subscription...")
        
        # Wait for connection and subscription (like run_continuation.py)
        time.sleep(3)
        
        # STEP 3: MONITOR TICKS - Set up tick handler and monitor
        print("\n=== STEP 3: MONITORING TICKS (10 seconds) ===")
        
        ticks_received = []
        
        def tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
            """Tick handler exactly like run_continuation.py"""
            tick_info = {
                'instrument_key': instrument_key,
                'symbol': symbol,
                'price': price,
                'timestamp': timestamp,
                'time_str': timestamp.strftime('%H:%M:%S.%f')[:-3]
            }
            ticks_received.append(tick_info)
            print(f"[TICK] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
        
        # Set the tick handler exactly like run_continuation.py
        data_streamer.tick_handler = tick_handler
        
        # Monitor ticks for 10 seconds
        print("Monitoring ticks for 10 seconds...")
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < 10:
            time.sleep(0.1)
        
        print(f"\n✅ RECEIVED {len(ticks_received)} ticks in 10 seconds")
        
        if len(ticks_received) == 0:
            print("❌ NO TICKS RECEIVED - Cannot test unsubscription!")
            print("   This could mean:")
            print("   - Market is closed")
            print("   - Stock has no trading activity")
            print("   - WebSocket connection issue")
            return False
        
        print("✅ SUCCESS: Ticks are being received!")
        
        # STEP 4: UNSUBSCRIBE - Use exact same method as run_continuation.py
        print("\n=== STEP 4: UNSUBSCRIBE ===")
        print("Calling data_streamer.unsubscribe() exactly like run_continuation.py...")
        
        try:
            data_streamer.unsubscribe([instrument_key])
            print("✅ Unsubscribe call completed")
        except Exception as e:
            print(f"❌ Unsubscribe error: {e}")
            return False
        
        # STEP 5: VERIFY - Monitor for ticks after unsubscription
        print("\n=== STEP 5: VERIFY NO TICKS AFTER UNSUBSCRIPTION (10 seconds) ===")
        
        ticks_after_unsub = []
        post_unsub_start = datetime.now()
        
        def tick_handler_after_unsub(instrument_key, symbol, price, timestamp, ohlc_list=None):
            """Tick handler to catch any ticks after unsubscription"""
            tick_info = {
                'instrument_key': instrument_key,
                'symbol': symbol,
                'price': price,
                'timestamp': timestamp,
                'time_str': timestamp.strftime('%H:%M:%S.%f')[:-3]
            }
            ticks_after_unsub.append(tick_info)
            print(f"[TICK AFTER UNSUB] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
        
        # Set new tick handler to catch any remaining ticks
        data_streamer.tick_handler = tick_handler_after_unsub
        
        # Monitor for 10 seconds after unsubscription
        print("Monitoring for any ticks after unsubscription...")
        while (datetime.now() - post_unsub_start).total_seconds() < 10:
            time.sleep(0.1)
        
        print(f"Received {len(ticks_after_unsub)} ticks after unsubscription")
        
        # STEP 6: RESULTS - Analyze the results
        print("\n=== TEST RESULTS ===")
        print(f"Ticks before unsubscription: {len(ticks_received)}")
        print(f"Ticks after unsubscription: {len(ticks_after_unsub)}")
        
        if len(ticks_after_unsub) == 0:
            print("✅ SUCCESS: No ticks received after unsubscription!")
            print("   The unsubscription mechanism is working correctly.")
            print("   This proves that data_streamer.unsubscribe() stops ticks.")
        else:
            print("❌ FAILURE: Still receiving ticks after unsubscription!")
            print("   This indicates a problem with the unsubscription mechanism.")
            print("   Possible causes:")
            print("   - Upstox delay in processing unsubscribe")
            print("   - WebSocket not properly handling unsubscribe")
            print("   - Tick handler still receiving data")
        
        print()
        print("=== REAL-WORLD SIMULATION COMPLETE ===")
        print("This test simulates exactly what happens in run_continuation.py:")
        print("1. SimpleStockStreamer connects to WebSocket")
        print("2. All stocks are automatically subscribed in on_open()")
        print("3. Ticks are received and processed via tick_handler")
        print("4. data_streamer.unsubscribe() is called for rejected stocks")
        print("5. Unsubscribed stocks should stop receiving ticks")
        print("6. This reduces resource usage and improves performance")
        
        # Cleanup
        try:
            data_streamer.disconnect()
            print("✅ WebSocket disconnected")
        except:
            pass
        
        return len(ticks_after_unsub) == 0
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("REAL UNSUBSCRIPTION TEST")
    print("Testing the exact unsubscription mechanism used in run_continuation.py")
    print("=" * 70)
    
    success = test_real_unsubscription()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 REAL UNSUBSCRIPTION TEST PASSED!")
        print("   The unsubscription mechanism is working correctly.")
        print("   You can trust that unsubscribed stocks stop receiving ticks.")
    else:
        print("❌ REAL UNSUBSCRIPTION TEST FAILED!")
        print("   There may be an issue with the unsubscription mechanism.")
        print("   Check the error messages above for more details.")
    print("=" * 70)

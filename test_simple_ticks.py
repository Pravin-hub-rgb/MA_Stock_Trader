#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Tick Logging Test
Step 1: Just subscribe and log ticks
"""

import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

def test_simple_ticks():
    """Just subscribe and log ticks"""
    
    print("=== SIMPLE TICK LOGGING TEST ===")
    print("Step 1: Subscribe and log ticks")
    print()
    
    try:
        # Import required modules
        from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer
        
        # Test with a single stock
        test_symbol = "ADANIPOWER"
        test_instrument_key = "NSE_EQ|INE049A01022"
        
        print(f"Testing with {test_symbol} ({test_instrument_key})")
        print()
        
        # Create data streamer
        data_streamer = SimpleStockStreamer([test_instrument_key], {test_instrument_key: test_symbol})
        
        # Track ticks received
        ticks_received = []
        
        def tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
            """Simple tick handler to log ticks"""
            tick_info = {
                'instrument_key': instrument_key,
                'symbol': symbol,
                'price': price,
                'timestamp': timestamp,
                'time_str': timestamp.strftime('%H:%M:%S.%f')[:-3]
            }
            
            ticks_received.append(tick_info)
            print(f"[TICK] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
        
        # Set the tick handler
        data_streamer.tick_handler = tick_handler
        
        # Connect to data stream
        print("Connecting to data stream...")
        if not data_streamer.connect():
            print("FAILED to connect to data stream")
            return False
        
        print("Connected! Waiting for ticks...")
        print()
        
        # Wait for initial connection
        time.sleep(3)
        
        # Monitor ticks for 20 seconds
        print("=== LOGGING TICKS (20 seconds) ===")
        start_time = datetime.now()
        monitor_duration = 20  # seconds
        
        while (datetime.now() - start_time).total_seconds() < monitor_duration:
            time.sleep(0.1)  # Small sleep to prevent busy waiting
        
        print(f"\nReceived {len(ticks_received)} ticks")
        
        if len(ticks_received) > 0:
            print("✅ SUCCESS: Ticks are being received!")
            print("Step 1 complete - we can receive ticks")
        else:
            print("❌ NO TICKS RECEIVED")
            print("There's an issue with tick reception")
        
        # Cleanup
        print()
        print("=== CLEANUP ===")
        try:
            data_streamer.disconnect()
            print("Disconnected from data stream")
        except Exception as e:
            print(f"Disconnect error: {e}")
        
        return len(ticks_received) > 0
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_ticks()
    if success:
        print("\n🎉 SIMPLE TICK LOGGING TEST PASSED!")
        print("Ready for Step 2: Unsubscription test")
    else:
        print("\n❌ SIMPLE TICK LOGGING TEST FAILED!")
        print("Need to fix tick reception first")
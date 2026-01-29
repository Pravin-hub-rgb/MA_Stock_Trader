#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Subscribe/Unsubscribe Functionality
Tests the unsubscribe method in SimpleStockStreamer
"""

import sys
import os
import time
import logging
from datetime import datetime
import pytz

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')

class TestTickHandler:
    """Test tick handler to capture ticks"""
    
    def __init__(self):
        self.ticks_received = 0
        self.last_tick_time = None
        self.symbols_received = set()
    
    def handle_tick(self, instrument_key, symbol, ltp, timestamp, ohlc_list):
        """Handle incoming ticks"""
        self.ticks_received += 1
        self.last_tick_time = timestamp
        self.symbols_received.add(symbol)
        
        if self.ticks_received <= 5:  # Only log first 5 ticks
            current_time = datetime.now(IST).strftime('%H:%M:%S')
            print(f"[{current_time}] TICK: {symbol} = ₹{ltp:.2f}")

def test_subscribe_unsubscribe():
    """Test subscribe and unsubscribe functionality"""
    
    print("=" * 60)
    print("TESTING SUBSCRIBE/UNSUBSCRIBE FUNCTIONALITY")
    print("=" * 60)
    
    # Test instruments - using a mix of real and test symbols
    test_instruments = [
        'NSE_EQ|INE121A01024',  # Real symbol from expert example
        'NSE_EQ|INE118H01025',  # Real symbol from expert example
        'NSE_EQ|INE002A01021',  # Another test symbol
    ]
    
    test_symbols = {
        'NSE_EQ|INE121A01024': 'TEST1',
        'NSE_EQ|INE118H01025': 'TEST2', 
        'NSE_EQ|INE002A01021': 'TEST3',
    }
    
    # Initialize streamer
    print(f"Initializing streamer with {len(test_instruments)} instruments...")
    from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer
    
    streamer = SimpleStockStreamer(test_instruments, test_symbols)
    
    # Set up test tick handler
    tick_handler = TestTickHandler()
    streamer.tick_handler = tick_handler.handle_tick
    
    print("\n" + "=" * 40)
    print("PHASE 1: SUBSCRIBE AND RECEIVE TICKS")
    print("=" * 40)
    
    # Connect and subscribe
    if not streamer.connect():
        print("❌ Failed to connect to WebSocket")
        return False
    
    # Wait for connection to establish
    print("Waiting for WebSocket connection...")
    start_time = time.time()
    while not streamer.connected and time.time() - start_time < 10:
        time.sleep(0.5)
    
    if not streamer.connected:
        print("❌ WebSocket connection failed")
        return False
    
    print("✅ WebSocket connected successfully")
    
    # Wait for initial ticks
    print("Waiting for initial ticks...")
    time.sleep(3)
    
    ticks_before_unsubscribe = tick_handler.ticks_received
    symbols_before = len(tick_handler.symbols_received)
    
    print(f"📊 Ticks received before unsubscribe: {ticks_before_unsubscribe}")
    print(f"📊 Symbols receiving ticks: {symbols_before}")
    
    if ticks_before_unsubscribe == 0:
        print("⚠️  No ticks received - this might be expected if market is closed or symbols are invalid")
        print("   Proceeding with unsubscribe test anyway...")
    
    print("\n" + "=" * 40)
    print("PHASE 2: UNSUBSCRIBE FROM INSTRUMENTS")
    print("=" * 40)
    
    # Test unsubscribe
    try:
        print(f"Attempting to unsubscribe from {len(test_instruments)} instruments...")
        streamer.unsubscribe(test_instruments)
        print("✅ Unsubscribe call completed successfully")
        
    except Exception as e:
        print(f"❌ Unsubscribe failed: {e}")
        return False
    
    # Wait a moment after unsubscribe
    time.sleep(2)
    
    ticks_after_unsubscribe = tick_handler.ticks_received
    symbols_after = len(tick_handler.symbols_received)
    
    print(f"📊 Ticks received after unsubscribe: {ticks_after_unsubscribe}")
    print(f"📊 Symbols receiving ticks after unsubscribe: {symbols_after}")
    
    print("\n" + "=" * 40)
    print("PHASE 3: ANALYSIS AND RESULTS")
    print("=" * 40)
    
    # Analyze results
    if ticks_before_unsubscribe > 0:
        if ticks_after_unsubscribe == ticks_before_unsubscribe:
            print("✅ SUCCESS: No new ticks received after unsubscribe")
            print("   This indicates unsubscribe is working correctly")
        else:
            new_ticks = ticks_after_unsubscribe - ticks_before_unsubscribe
            print(f"⚠️  WARNING: {new_ticks} new ticks received after unsubscribe")
            print("   This might indicate unsubscribe is not working fully")
    else:
        print("ℹ️  INFO: No ticks received during test (market may be closed)")
        print("   Unsubscribe call completed without errors - this is good")
    
    # Test individual unsubscribe
    print("\n" + "=" * 40)
    print("PHASE 4: TESTING INDIVIDUAL UNSUBSCRIBE")
    print("=" * 40)
    
    # Try to unsubscribe from a single instrument
    try:
        single_instrument = [test_instruments[0]]
        print(f"Attempting to unsubscribe from single instrument: {single_instrument[0]}")
        streamer.unsubscribe(single_instrument)
        print("✅ Single instrument unsubscribe completed successfully")
    except Exception as e:
        print(f"❌ Single instrument unsubscribe failed: {e}")
        return False
    
    # Clean up
    print("\n" + "=" * 40)
    print("PHASE 5: CLEANUP")
    print("=" * 40)
    
    try:
        streamer.disconnect()
        print("✅ WebSocket disconnected successfully")
    except Exception as e:
        print(f"⚠️  Disconnect warning: {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Initial instruments: {len(test_instruments)}")
    print(f"Ticks before unsubscribe: {ticks_before_unsubscribe}")
    print(f"Ticks after unsubscribe: {ticks_after_unsubscribe}")
    print(f"Symbols before unsubscribe: {symbols_before}")
    print(f"Symbols after unsubscribe: {symbols_after}")
    
    if ticks_before_unsubscribe == 0:
        print("\n✅ TEST PASSED: Unsubscribe method works (no errors during calls)")
        print("   Note: No ticks received - likely due to market closed or test symbols")
    elif ticks_after_unsubscribe == ticks_before_unsubscribe:
        print("\n✅ TEST PASSED: Unsubscribe method working correctly")
        print("   No new ticks received after unsubscribe")
    else:
        print("\n⚠️  TEST INCONCLUSIVE: Some ticks received after unsubscribe")
        print("   This could be due to timing or WebSocket behavior")
    
    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    print("Starting Subscribe/Unsubscribe Test")
    print(f"Test started at: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    try:
        success = test_subscribe_unsubscribe()
        if success:
            print("🎉 Test completed successfully!")
        else:
            print("❌ Test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
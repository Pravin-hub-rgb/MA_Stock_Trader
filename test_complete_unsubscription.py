#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Unsubscription Test
Tests the full unsubscription flow including actual Upstox unsubscribe call
"""

import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

def test_complete_unsubscription():
    """Test complete unsubscription flow with real Upstox unsubscribe"""
    
    print("=== COMPLETE UNSUBSCRIPTION TEST ===")
    print("Testing full flow: subscribe -> receive ticks -> unsubscribe -> verify no more ticks")
    print()
    
    try:
        # Import required modules
        from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer
        
        # Test with a single stock
        test_symbol = "ADANIPOWER"  # Use a stock that's likely to have data
        test_instrument_key = "NSE_EQ|INE049A01022"  # ADANIPOWER instrument key
        
        print(f"Testing with {test_symbol} ({test_instrument_key})")
        print()
        
        # Create data streamer
        data_streamer = SimpleStockStreamer([test_instrument_key], {test_instrument_key: test_symbol})
        
        # Track ticks received
        ticks_received = []
        ticks_after_unsub = []
        unsub_time = None
        
        def tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
            """Simple tick handler to track received ticks"""
            tick_info = {
                'instrument_key': instrument_key,
                'symbol': symbol,
                'price': price,
                'timestamp': timestamp,
                'time_str': timestamp.strftime('%H:%M:%S.%f')[:-3]
            }
            
            # Determine if this tick came before or after unsubscription
            if unsub_time and timestamp > unsub_time:
                ticks_after_unsub.append(tick_info)
                print(f"[AFTER UNSUB] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
            else:
                ticks_received.append(tick_info)
                print(f"[BEFORE UNSUB] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
        
        # Set the tick handler
        data_streamer.tick_handler = tick_handler
        
        # Connect to data stream
        print("Connecting to data stream...")
        if not data_streamer.connect():
            print("FAILED to connect to data stream")
            return False
        
        print("Connected! Waiting for ticks...")
        print()
        
        # Wait for initial connection and first ticks
        time.sleep(5)  # Wait longer for connection to stabilize
        
        # Monitor ticks for 15 seconds before unsubscription
        print("=== PHASE 1: MONITORING TICKS (15 seconds) ===")
        start_time = datetime.now()
        monitor_duration = 15  # seconds
        
        while (datetime.now() - start_time).total_seconds() < monitor_duration:
            time.sleep(0.1)  # Small sleep to prevent busy waiting
        
        print(f"Received {len(ticks_received)} ticks before unsubscription")
        print()
        
        # Check if we actually received any ticks
        if len(ticks_received) == 0:
            print("❌ NO TICKS RECEIVED - Cannot test unsubscription!")
            print("   This suggests an issue with tick reception, not unsubscription.")
            print("   The test needs to receive ticks first to verify unsubscription works.")
            return False
        
        # Now unsubscribe
        print("=== PHASE 2: UNSUBSCRIBING ===")
        unsub_time = datetime.now()
        print(f"Unsubscribing at {unsub_time.strftime('%H:%M:%S.%f')[:-3]}")
        
        try:
            data_streamer.unsubscribe([test_instrument_key])
            print("Unsubscribe call completed")
        except Exception as e:
            print(f"Unsubscribe error: {e}")
            return False
        
        print()
        
        # Monitor for 15 seconds after unsubscription
        print("=== PHASE 3: MONITORING AFTER UNSUBSCRIPTION (15 seconds) ===")
        post_unsub_start = datetime.now()
        post_unsub_duration = 15  # seconds
        
        while (datetime.now() - post_unsub_start).total_seconds() < post_unsub_duration:
            time.sleep(0.1)  # Small sleep to prevent busy waiting
        
        print(f"Received {len(ticks_after_unsub)} ticks after unsubscription")
        print()
        
        # Results analysis
        print("=== TEST RESULTS ===")
        print(f"Ticks before unsubscription: {len(ticks_received)}")
        print(f"Ticks after unsubscription: {len(ticks_after_unsub)}")
        
        if len(ticks_after_unsub) == 0:
            print("✅ SUCCESS: No ticks received after unsubscription!")
            print("   The complete unsubscription flow is working correctly.")
            print("   Both application-level and Upstox-level unsubscription are working.")
        else:
            print("❌ FAILURE: Still receiving ticks after unsubscription!")
            print("   There may be a delay in Upstox stopping the data flow.")
            print("   Or the unsubscription call didn't work properly.")
            print()
            print("First few ticks after unsubscription:")
            for tick in ticks_after_unsub[:5]:  # Show first 5 ticks
                print(f"   {tick['time_str']} - {tick['symbol']}: Rs{tick['price']:.2f}")
        
        # Cleanup
        print()
        print("=== CLEANUP ===")
        try:
            data_streamer.disconnect()
            print("Disconnected from data stream")
        except Exception as e:
            print(f"Disconnect error: {e}")
        
        return len(ticks_after_unsub) == 0
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_unsubscription()
    if success:
        print("\n🎉 COMPLETE UNSUBSCRIPTION TEST PASSED!")
        print("The full unsubscription flow is working correctly.")
    else:
        print("\n❌ COMPLETE UNSUBSCRIPTION TEST FAILED!")
        print("There may be an issue with the complete unsubscription behavior.")
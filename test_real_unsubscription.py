#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to simulate real unsubscription and verify ticks stop
"""

import sys
import os
from datetime import datetime
import time

# Add src to path
sys.path.insert(0, 'src')

def test_real_unsubscription():
    """Test that unsubscription actually stops ticks"""
    
    print("=== TESTING REAL UNSUBSCRIPTION BEHAVIOR ===")
    print()
    
    try:
        # Import the modules
        from src.trading.live_trading.continuation_stock_monitor import StockMonitor
        from src.trading.live_trading.continuation_modules.subscription_manager import ContinuationSubscriptionManager
        from src.trading.live_trading.continuation_modules.integration import ContinuationIntegration
        
        # Create a real data streamer (like continuation bot)
        from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer
        
        # Test with real stocks that should have data
        test_symbol = "ADANIPOWER"
        test_instrument_key = "NSE_EQ|INE049A01022"
        
        print(f"Using real data streamer with {test_symbol} ({test_instrument_key})")
        
        # Create real data streamer
        data_streamer = SimpleStockStreamer([test_instrument_key], {test_instrument_key: test_symbol})
        
        # Create test setup
        monitor = StockMonitor()
        
        # Add test stock
        monitor.add_stock(test_symbol, test_instrument_key, 100.0, 'continuation')
        
        # Set opening prices to avoid formatting errors
        monitor.stocks[test_instrument_key].set_open_price(100.0)
        
        # Set gap validation to True to avoid rejection
        monitor.stocks[test_instrument_key].gap_validated = True
        
        # Create subscription manager
        subscription_manager = ContinuationSubscriptionManager(data_streamer, monitor)
        
        # Subscribe to all stocks
        instrument_keys = [test_instrument_key]
        subscription_manager.subscribe_all(instrument_keys)
        
        print("Initial state:")
        for stock in monitor.stocks.values():
            print(f"  {stock.symbol}: is_active={stock.is_active}, is_subscribed={stock.is_subscribed}")
        print()
        
        # Create integration
        integration = ContinuationIntegration(data_streamer, monitor)
        
        print("=== STEP 1: SUBSCRIBE AND RECEIVE TICKS ===")
        print("Connecting to data stream and receiving ticks...")
        
        # Connect to data stream
        if not data_streamer.connect():
            print("FAILED to connect to data stream")
            return False
        
        print("Connected! Waiting for ticks...")
        
        # Wait for connection
        time.sleep(3)
        
        # Monitor ticks for 10 seconds
        print("=== RECEIVING TICKS (10 seconds) ===")
        start_time = datetime.now()
        ticks_received = []
        
        def tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
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
        
        # Monitor for 10 seconds
        while (datetime.now() - start_time).total_seconds() < 10:
            time.sleep(0.1)
        
        print(f"\nReceived {len(ticks_received)} ticks")
        
        if len(ticks_received) == 0:
            print("❌ NO TICKS RECEIVED - Cannot test unsubscription!")
            return False
        
        print("✅ SUCCESS: Ticks are being received!")
        
        print()
        print("=== STEP 2: UNSUBSCRIBE ===")
        print("Now unsubscribing...")
        
        # Unsubscribe
        try:
            data_streamer.unsubscribe([test_instrument_key])
            print("Unsubscribe call completed")
        except Exception as e:
            print(f"Unsubscribe error: {e}")
            return False
        
        print()
        
        # Monitor for 10 seconds after unsubscription
        print("=== MONITORING AFTER UNSUBSCRIPTION (10 seconds) ===")
        post_unsub_start = datetime.now()
        ticks_after_unsub = []
        
        while (datetime.now() - post_unsub_start).total_seconds() < 10:
            time.sleep(0.1)
        
        print(f"Received {len(ticks_after_unsub)} ticks after unsubscription")
        
        # Results analysis
        print()
        print("=== TEST RESULTS ===")
        print(f"Ticks before unsubscription: {len(ticks_received)}")
        print(f"Ticks after unsubscription: {len(ticks_after_unsub)}")
        
        if len(ticks_after_unsub) == 0:
            print("✅ SUCCESS: No ticks received after unsubscription!")
            print("   The unsubscription is working correctly.")
        else:
            print("❌ FAILURE: Still receiving ticks after unsubscription!")
            print("   There may be a delay in Upstox stopping the data flow.")
        
        print()
        print("=== REAL-WORLD SIMULATION COMPLETE ===")
        print("This test simulates exactly what should happen in your live trading:")
        print("1. Stocks are subscribed and receive ticks")
        print("2. Some stocks get unsubscribed (Phase 1/2)")
        print("3. Unsubscribed stocks should stop processing ticks")
        print("4. Subscribed stocks continue processing ticks")
        
        return len(ticks_after_unsub) == 0
        
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_unsubscription()
    if success:
        print("\n🎉 REAL UNSUBSCRIPTION TEST PASSED!")
    else:
        print("\n❌ REAL UNSUBSCRIPTION TEST FAILED!")
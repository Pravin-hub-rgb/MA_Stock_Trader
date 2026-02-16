#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the subscription tracking discrepancy fix
Tests that the data streamer correctly tracks only validated instruments
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src/trading/live_trading')

def test_subscription_tracking_fix():
    """Test that subscription tracking discrepancy is fixed"""
    print("=== SUBSCRIPTION TRACKING DISCREPANCY FIX TEST ===")
    
    # Test 1: Check that data streamer has update_active_instruments method
    print("\n1. Testing data streamer update_active_instruments method...")
    try:
        from simple_data_streamer import SimpleStockStreamer
        
        # Create a mock data streamer with 13 instruments
        instrument_keys = [f"NSE_EQ|{i}" for i in range(13)]
        stock_symbols = {key: f"STOCK{i}" for i, key in enumerate(instrument_keys)}
        
        streamer = SimpleStockStreamer(instrument_keys, stock_symbols)
        
        # Check initial state
        if len(streamer.active_instruments) == 13:
            print("✅ Initial active instruments: 13 (all instruments)")
        else:
            print(f"❌ Initial active instruments: {len(streamer.active_instruments)} (expected 13)")
            return False
        
        # Test update with 4 validated instruments (simulating the optimization)
        validated_keys = instrument_keys[:4]  # Simulate 4 validated out of 13
        streamer.update_active_instruments(validated_keys)
        
        if len(streamer.active_instruments) == 4:
            print("✅ After update: 4 active instruments (validated only)")
        else:
            print(f"❌ After update: {len(streamer.active_instruments)} active instruments (expected 4)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing data streamer: {e}")
        return False
    
    # Test 2: Check that integration calls update_active_instruments
    print("\n2. Testing integration prepare_and_subscribe method...")
    try:
        from continuation_modules.integration import ContinuationIntegration
        from continuation_stock_monitor import StockMonitor
        from simple_data_streamer import SimpleStockStreamer
        
        # Create mock components
        instrument_keys = [f"NSE_EQ|{i}" for i in range(13)]
        stock_symbols = {key: f"STOCK{i}" for i, key in enumerate(instrument_keys)}
        streamer = SimpleStockStreamer(instrument_keys, stock_symbols)
        monitor = StockMonitor()
        
        # Add mock stocks to monitor
        for i, key in enumerate(instrument_keys):
            symbol = f"STOCK{i}"
            monitor.add_stock(symbol, key, 100.0, 'continuation')
        
        # Create integration
        integration = ContinuationIntegration(streamer, monitor)
        
        # Test with 4 validated instruments
        validated_keys = instrument_keys[:4]
        integration.prepare_and_subscribe(validated_keys)
        
        # Check that data streamer was updated
        if len(streamer.active_instruments) == 4:
            print("✅ Integration correctly updated data streamer to 4 instruments")
        else:
            print(f"❌ Integration updated data streamer to {len(streamer.active_instruments)} instruments (expected 4)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        return False
    
    # Test 3: Check unsubscribe message accuracy
    print("\n3. Testing unsubscribe message accuracy...")
    try:
        # Simulate the scenario from the user's log
        # Start with 4 validated instruments, unsubscribe 2, should show 2 remaining
        
        instrument_keys = [f"NSE_EQ|{i}" for i in range(4)]  # 4 validated
        stock_symbols = {key: f"STOCK{i}" for i, key in enumerate(instrument_keys)}
        streamer = SimpleStockStreamer(instrument_keys, stock_symbols)
        
        # First update to validated instruments (simulating the optimization)
        validated_keys = instrument_keys[:4]  # All 4 are validated
        streamer.update_active_instruments(validated_keys)
        
        # Simulate 2 instruments being unsubscribed
        unsubscribed_keys = instrument_keys[:2]
        print(f"Before unsubscribe: {len(streamer.active_instruments)} active instruments")
        print(f"Unsubscribing: {unsubscribed_keys}")
        streamer.unsubscribe(unsubscribed_keys)
        print(f"After unsubscribe: {len(streamer.active_instruments)} active instruments")
        
        # Check remaining count
        remaining = len(streamer.active_instruments)
        if remaining == 2:
            print("✅ Unsubscribe message shows correct remaining count: 2")
        else:
            print(f"❌ Unsubscribe message shows incorrect remaining count: {remaining} (expected 2)")
            return False
            
    except Exception as e:
        print(f"❌ Error testing unsubscribe accuracy: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    print("✅ Subscription tracking discrepancy fix is working correctly")
    print("✅ Data streamer now tracks only validated instruments")
    print("✅ Unsubscribe messages will show accurate remaining counts")
    print("✅ No more 'Active instruments remaining: 11' when only 4 were validated")
    return True

def simulate_fixed_flow():
    """Simulate the fixed subscription flow"""
    print("\n=== SIMULATED FIXED FLOW ===")
    
    print("BEFORE FIX (problematic):")
    print("1. Data streamer initialized with 13 instruments")
    print("2. Only 4 validated stocks subscribed")
    print("3. 2 stocks enter positions, get unsubscribed")
    print("4. System reports: 'Active instruments remaining: 11' (WRONG!)")
    print("   Because it tracked all 13, not just the 4 validated ones")
    
    print("\nAFTER FIX (correct):")
    print("1. Data streamer initialized with 13 instruments")
    print("2. Only 4 validated stocks subscribed")
    print("3. Data streamer updated to track only 4 validated instruments")
    print("4. 2 stocks enter positions, get unsubscribed")
    print("5. System reports: 'Active instruments remaining: 2' (CORRECT!)")
    print("   Because it only tracks the 4 validated instruments")
    
    print("\nFIX IMPLEMENTED:")
    print("✅ Added update_active_instruments() method to SimpleStockStreamer")
    print("✅ Integration.prepare_and_subscribe() calls update_active_instruments()")
    print("✅ Data streamer now tracks only validated instruments")
    print("✅ Unsubscribe messages show accurate remaining counts")

if __name__ == "__main__":
    print("SUBSCRIPTION TRACKING DISCREPANCY FIX VERIFICATION")
    print("=" * 55)
    
    success = test_subscription_tracking_fix()
    if success:
        simulate_fixed_flow()
    else:
        print("\n❌ SUBSCRIPTION TRACKING FIX VERIFICATION FAILED")
        print("Please check the implementation and try again.")
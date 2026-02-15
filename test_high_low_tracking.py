#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify high/low tracking fix for continuation trading
"""

import sys
import os
from datetime import datetime
import pytz

# Add src to path
sys.path.insert(0, 'src')

def test_high_low_tracking():
    """Test the high/low tracking functionality"""
    
    print("=== TESTING HIGH/LOW TRACKING FIX ===")
    print()
    
    # Import required modules
    from trading.live_trading.continuation_modules.tick_processor import ContinuationTickProcessor
    from trading.live_trading.continuation_stock_monitor import StockState
    
    # Create a test stock
    stock = StockState(
        symbol="TESTSTOCK",
        instrument_key="NSE_EQ|TESTSTOCK",
        previous_close=100.0,
        situation='continuation'
    )
    
    # Set opening price (simulating IEP)
    stock.set_open_price(102.0)
    
    # Create tick processor
    processor = ContinuationTickProcessor(stock)
    
    print(f"Initial state:")
    print(f"  Open Price: Rs{stock.open_price:.2f}")
    print(f"  Daily High: Rs{stock.daily_high:.2f}")
    print(f"  Daily Low: Rs{stock.daily_low:.2f}")
    print(f"  Entry High: {stock.entry_high}")
    print(f"  Entry SL: {stock.entry_sl}")
    print()
    
    # Simulate price movements
    test_prices = [
        101.5,  # Below open
        103.0,  # Above open, new high
        102.8,  # Below previous high
        104.5,  # New high
        103.2,  # Below previous high
        105.0,  # New high
    ]
    
    print("Simulating price movements:")
    for i, price in enumerate(test_prices):
        timestamp = datetime.now(pytz.timezone('Asia/Kolkata'))
        
        print(f"Tick {i+1}: Price = Rs{price:.2f}")
        
        # Process the tick
        processor.process_tick(price, timestamp)
        
        print(f"  After processing:")
        print(f"    Daily High: Rs{stock.daily_high:.2f}")
        print(f"    Daily Low: Rs{stock.daily_low:.2f}")
        print(f"    Entry High: Rs{stock.entry_high:.2f}")
        print(f"    Entry SL: Rs{stock.entry_sl:.2f}")
        print()
    
    # Test the key scenarios
    print("=== TEST RESULTS ===")
    
    # Test 1: High tracking works
    if stock.daily_high == 105.0:
        print("✓ PASS: Daily high correctly tracked to Rs105.00")
    else:
        print(f"✗ FAIL: Daily high is Rs{stock.daily_high:.2f}, expected Rs105.00")
    
    # Test 2: Entry high follows daily high
    if stock.entry_high == 105.0:
        print("✓ PASS: Entry high correctly follows daily high")
    else:
        print(f"✗ FAIL: Entry high is Rs{stock.entry_high:.2f}, expected Rs105.00")
    
    # Test 3: SL is calculated correctly
    expected_sl = 105.0 * 0.96  # 4% below entry
    if abs(stock.entry_sl - expected_sl) < 0.01:
        print(f"✓ PASS: Entry SL correctly calculated as Rs{stock.entry_sl:.2f}")
    else:
        print(f"✗ FAIL: Entry SL is Rs{stock.entry_sl:.2f}, expected Rs{expected_sl:.2f}")
    
    # Test 4: Low tracking works
    if stock.daily_low == 101.5:
        print("✓ PASS: Daily low correctly tracked to Rs101.50")
    else:
        print(f"✗ FAIL: Daily low is Rs{stock.daily_low:.2f}, expected Rs101.50")
    
    print()
    print("=== TEST COMPLETE ===")
    
    # Summary
    all_tests_passed = (
        stock.daily_high == 105.0 and
        stock.entry_high == 105.0 and
        abs(stock.entry_sl - expected_sl) < 0.01 and
        stock.daily_low == 101.5
    )
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! High/low tracking fix is working correctly.")
        return True
    else:
        print("❌ SOME TESTS FAILED! Please review the implementation.")
        return False

if __name__ == "__main__":
    success = test_high_low_tracking()
    sys.exit(0 if success else 1)
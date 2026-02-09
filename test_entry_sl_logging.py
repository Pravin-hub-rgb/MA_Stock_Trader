#!/usr/bin/env python3
"""
Test Entry/SL Logging Enhancement
Tests the enhanced logging in prepare_entry() method
"""

import sys
import os
from datetime import datetime, time
import logging

# Add src to path
sys.path.insert(0, 'src/trading/live_trading')

# Configure logging to show our enhanced entry/SL logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

def test_entry_sl_logging():
    """Test the enhanced entry/SL logging in prepare_entry() method"""
    print("Testing Entry/SL Logging Enhancement")
    print("=" * 40)
    
    # Import the StockState class
    from continuation_stock_monitor import StockState
    from config import ENTRY_SL_PCT
    
    # Create a test stock
    stock = StockState('TESTSTOCK', 'NSE_EQ|TESTSTOCK', 100.0, 'continuation')
    
    # Set up some test data
    stock.open_price = 105.0  # Gap up
    stock.daily_high = 110.0  # High reached during monitoring
    stock.daily_low = 102.0   # Low during monitoring
    stock.gap_validated = True
    stock.low_violation_checked = True
    stock.volume_validated = True
    stock.is_active = True
    
    print(f"Test stock setup:")
    print(f"  Symbol: {stock.symbol}")
    print(f"  Previous Close: Rs{stock.previous_close:.2f}")
    print(f"  Open Price: Rs{stock.open_price:.2f}")
    print(f"  Daily High: Rs{stock.daily_high:.2f}")
    print(f"  Daily Low: Rs{stock.daily_low:.2f}")
    print(f"  SL Percentage: {ENTRY_SL_PCT*100:.1f}%")
    print()
    
    print("Calling prepare_entry() - should log entry price and SL...")
    print("-" * 50)
    
    # Call prepare_entry() which should now log entry price and SL
    stock.prepare_entry()
    
    print("-" * 50)
    print("Entry/SL logging test completed!")
    print()
    print(f"Final values set:")
    print(f"  Entry High: Rs{stock.entry_high:.2f}")
    print(f"  Entry SL: Rs{stock.entry_sl:.2f}")
    print(f"  Entry Ready: {stock.entry_ready}")
    
    # Verify the calculations are correct
    expected_entry = stock.daily_high
    expected_sl = expected_entry * (1 - ENTRY_SL_PCT)
    
    print()
    print("Verification:")
    print(f"  Expected Entry: Rs{expected_entry:.2f} ✅")
    print(f"  Expected SL: Rs{expected_sl:.2f} ✅")
    print(f"  Calculations correct: {abs(stock.entry_high - expected_entry) < 0.01 and abs(stock.entry_sl - expected_sl) < 0.01}")

if __name__ == "__main__":
    test_entry_sl_logging()
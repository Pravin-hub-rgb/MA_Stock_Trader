#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to isolate and verify high/low monitoring functionality
"""

import sys
import os
from datetime import datetime
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the ReversalStockState class
from src.trading.live_trading.reversal_stock_monitor import ReversalStockState

def test_high_low_monitoring():
    """Test high/low monitoring with live price updates"""
    
    print("=== TESTING HIGH/LOW MONITORING ===")
    
    # Create a test stock (Strong Start)
    symbol = "RELIANCE"
    instrument_key = "NSE_EQ|RELIANCE"
    previous_close = 2800.0
    situation = "reversal_s1"
    
    # Create stock state
    stock = ReversalStockState(symbol, instrument_key, previous_close, situation)
    
    # Set opening price
    stock.set_open_price(2850.0)
    stock.gap_validated = True
    stock.low_violation_checked = True
    
    print(f"Created {symbol} - Open: {stock.open_price}, Situation: {stock.situation}")
    
    # Test price updates
    test_prices = [
        2855.0,  # Price goes up
        2860.0,  # Price goes higher
        2858.0,  # Price comes down slightly
        2865.0,  # Price goes to new high
        2845.0,  # Price drops
        2870.0,  # Price goes to new high
    ]
    
    print("\n=== TESTING PRICE UPDATES ===")
    for i, price in enumerate(test_prices):
        timestamp = datetime.now()
        stock.update_price(price, timestamp)
        
        print(f"Tick {i+1}: Price={price:.2f}, High={stock.daily_high:.2f}, Low={stock.daily_low:.2f}")
        
        # Test prepare_entry_ss after a few ticks
        if i == 2:
            print(f"\n=== TESTING prepare_entry_ss() CALL ===")
            stock.prepare_entry_ss()
            print(f"After prepare_entry_ss(): entry_high={stock.entry_high}, entry_sl={stock.entry_sl}")
        
        # Test prepare_entry() method flow
        if i == 3:
            print(f"\n=== TESTING prepare_entry() CALL ===")
            stock.prepare_entry()
            print(f"After prepare_entry(): entry_high={stock.entry_high}, entry_sl={stock.entry_sl}")
        
        # Test update_entry_levels after prepare_entry_ss
        if i >= 2:
            print(f"\n=== TESTING update_entry_levels() CALL ===")
            stock.update_entry_levels()
            print(f"After update_entry_levels(): entry_high={stock.entry_high}, entry_sl={stock.entry_sl}")
    
    print(f"\n=== FINAL STATUS ===")
    print(f"Symbol: {stock.symbol}")
    print(f"Situation: {stock.situation}")
    print(f"Open Price: {stock.open_price}")
    print(f"Current Price: {stock.current_price}")
    print(f"Daily High: {stock.daily_high}")
    print(f"Daily Low: {stock.daily_low}")
    print(f"Entry High: {stock.entry_high}")
    print(f"Entry SL: {stock.entry_sl}")
    print(f"Entry Ready: {stock.entry_ready}")

if __name__ == "__main__":
    test_high_low_monitoring()
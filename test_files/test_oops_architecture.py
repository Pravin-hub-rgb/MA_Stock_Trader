#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify OOPS candidates don't monitor high/low unnecessarily
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

# Import the ReversalStockState and ReversalTickProcessor classes
from src.trading.live_trading.reversal_stock_monitor import ReversalStockState
from src.trading.live_trading.reversal_modules.tick_processor import ReversalTickProcessor

def test_oops_architecture():
    """Test that OOPS candidates don't monitor high/low unnecessarily"""
    
    print("=== TESTING OOPS ARCHITECTURE ===")
    
    # Create a test stock (OOPS)
    symbol = "GARUDA"
    instrument_key = "NSE_EQ|GARUDA"
    previous_close = 160.80
    situation = "reversal_s2"
    
    # Create stock state
    stock = ReversalStockState(symbol, instrument_key, previous_close, situation)
    
    # Set opening price (gap down)
    stock.set_open_price(157.35)
    stock.gap_validated = True
    stock.low_violation_checked = True
    
    print(f"Created {symbol} - Open: {stock.open_price}, Situation: {stock.situation}")
    
    # Create tick processor
    tick_processor = ReversalTickProcessor(stock)
    
    # Test price updates through tick processor
    test_prices = [
        157.50,  # Price goes up slightly
        158.00,  # Price goes higher
        157.80,  # Price comes down slightly
        158.50,  # Price goes to new high
        157.00,  # Price drops
        161.00,  # Price crosses previous close (OOPS trigger)
    ]
    
    print("\n=== TESTING OOPS ARCHITECTURE ===")
    for i, price in enumerate(test_prices):
        timestamp = datetime.now()
        
        print(f"\nTick {i+1}: Price={price:.2f}")
        print(f"Before: High={stock.daily_high:.2f}, Low={stock.daily_low:.2f}, entry_high={stock.entry_high}, entry_sl={stock.entry_sl}")
        
        # Process tick through tick processor
        tick_processor.process_tick(price, timestamp)
        
        print(f"After:  High={stock.daily_high:.2f}, Low={stock.daily_low:.2f}, entry_high={stock.entry_high}, entry_sl={stock.entry_sl}")
    
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
    print(f"Entered: {stock.entered}")

if __name__ == "__main__":
    test_oops_architecture()
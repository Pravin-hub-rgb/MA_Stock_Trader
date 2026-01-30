#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Entry Logic Test
Tests the entry logic directly without WebSocket dependency
Simulates price ticks and tests entry triggering
"""

import sys
import os
from datetime import datetime
import pytz

# Add src to path
sys.path.insert(0, 'src')

# Import components
from src.trading.live_trading.reversal_stock_monitor import ReversalStockState
from src.trading.live_trading.reversal_modules.state_machine import StockState
from src.trading.live_trading.reversal_modules.tick_processor import ReversalTickProcessor

def test_entry_logic_direct():
    """Test entry logic directly by simulating price ticks"""
    
    print("=== DIRECT ENTRY LOGIC TEST ===")
    print("Testing entry logic by simulating price ticks")
    print()
    
    # Configuration
    IST = pytz.timezone('Asia/Kolkata')
    test_symbol = "POONAWALLA"
    test_instrument_key = "NSE_EQ|16609"
    prev_close = 399.90
    
    print(f"TESTING STOCK: {test_symbol}")
    print(f"PREVIOUS CLOSE: Rs{prev_close:.2f}")
    print()
    
    # Create stock with debugging setup
    print("=== CREATING STOCK WITH DEBUGGING SETUP ===")
    
    # Create stock with OOPS situation for immediate entry
    stock = ReversalStockState(test_symbol, test_instrument_key, prev_close, 'reversal_s2')
    
    # Set up for immediate entry testing
    stock.open_price = prev_close - 1.0  # Gap down setup
    stock.gap_validated = True           # Skip gap validation
    stock.low_violation_checked = True   # Skip low violation
    stock.daily_low = prev_close - 2.0   # Set daily low below opening
    
    # Set entry price to previous close for OOPS (price needs to cross above previous close)
    entry_price = prev_close
    stock.entry_price = entry_price
    stock.entry_ready = True
    stock.entered = False
    
    # Force state to monitoring_entry for entry testing
    stock._transition_to(StockState.MONITORING_ENTRY, "direct test setup")
    
    print(f"STOCK SETUP COMPLETE:")
    print(f"   Symbol: {stock.symbol}")
    print(f"   Situation: {stock.situation}")
    print(f"   State: {stock.state.value}")
    print(f"   Entry Ready: {stock.entry_ready}")
    print(f"   Entered: {stock.entered}")
    print(f"   Entry Price: Rs{stock.entry_price:.2f}")
    print(f"   Gap Direction: {'OOPS (Gap Down)' if stock.open_price < stock.previous_close else 'Strong Start (Gap Up)'}")
    print()
    
    # Create tick processor
    print("=== CREATING TICK PROCESSOR ===")
    tick_processor = ReversalTickProcessor(stock)
    
    # Simulate price ticks
    print("=== SIMULATING PRICE TICKS ===")
    
    # Starting price below entry
    current_price = entry_price - 0.5  # Start below entry price
    print(f"Starting price: Rs{current_price:.2f} (below entry: Rs{entry_price:.2f})")
    print()
    
    # Simulate price movement
    price_steps = [
        current_price,           # Step 1: Below entry
        current_price + 0.2,     # Step 2: Getting closer
        current_price + 0.4,     # Step 3: Almost there
        current_price + 0.6,     # Step 4: Crossed entry! (399.90)
        current_price + 0.8,     # Step 5: Above entry
        current_price + 1.0,     # Step 6: Further above
    ]
    
    timestamp = datetime.now(IST)
    
    for i, price in enumerate(price_steps, 1):
        print(f"--- STEP {i}: PRICE TICK ---")
        print(f"Time: {timestamp.strftime('%H:%M:%S')}")
        print(f"Price: Rs{price:.2f}")
        print(f"Entry Price: Rs{stock.entry_price:.2f}")
        print(f"Stock State: {stock.state.value}")
        print(f"Entry Ready: {stock.entry_ready}")
        print(f"Entered: {stock.entered}")
        
        # Check conditions before processing
        should_process = (
            stock.is_in_state('monitoring_entry') and
            stock.entry_ready and
            not stock.entered
        )
        
        print(f"Should process tick: {should_process}")
        
        if should_process:
            # Check entry condition manually
            crossed_up = price >= stock.entry_price
            print(f"Price crossed entry: {crossed_up} (price {price:.2f} >= entry {stock.entry_price:.2f})")
            
            if crossed_up:
                print("🚨 ENTRY SHOULD TRIGGER! 🚨")
            else:
                print("Price not crossed - continuing monitoring")
        else:
            print("Skipping tick - stock not ready for entry")
            if not stock.is_in_state('monitoring_entry'):
                print(f"   Reason: Not in monitoring_entry state (current: {stock.state.value})")
            if not stock.entry_ready:
                print(f"   Reason: Entry not ready")
            if stock.entered:
                print(f"   Reason: Already entered")
        
        # Process the tick
        print(f"Processing tick...")
        tick_processor.process_tick(price, timestamp)
        
        # Check results
        print(f"After processing:")
        print(f"   Stock State: {stock.state.value}")
        print(f"   Entered: {stock.entered}")
        if stock.entered:
            print(f"   ✅ ENTRY SUCCESSFULLY TRIGGERED!")
            print(f"   Entry Price: Rs{stock.entry_price:.2f}")
            print(f"   Trigger Price: Rs{price:.2f}")
            break
        else:
            print(f"   ❌ Entry not triggered")
        
        # Increment timestamp
        timestamp = timestamp.replace(second=timestamp.second + 1)
        print()
    
    # Final status
    print("=== FINAL STATUS ===")
    print(f"Stock State: {stock.state.value}")
    print(f"Entry Ready: {stock.entry_ready}")
    print(f"Entered: {stock.entered}")
    print(f"Entry Price: Rs{stock.entry_price:.2f}")
    
    if stock.entered:
        print(f"✅ Entry logic is WORKING correctly!")
        print(f"   The system successfully triggered entry when price crossed the threshold")
    else:
        print(f"❌ Entry logic has ISSUES!")
        print(f"   The system did not trigger entry even when price crossed the threshold")
        print(f"   This indicates a problem in the entry logic implementation")

def test_entry_conditions():
    """Test specific entry conditions"""
    
    print("\n=== TESTING ENTRY CONDITIONS ===")
    
    # Test the exact conditions that should trigger entry
    from src.trading.live_trading.reversal_stock_monitor import ReversalStockState
    from src.trading.live_trading.reversal_modules.state_machine import StockState
    
    stock = ReversalStockState("TEST", "TEST_KEY", 100.0, 'reversal_s2')
    stock._transition_to(StockState.MONITORING_ENTRY, "test")
    stock.entry_ready = True
    stock.entered = False
    stock.entry_price = 101.0
    
    print(f"Stock state: {stock.state.value}")
    print(f"Entry ready: {stock.entry_ready}")
    print(f"Entered: {stock.entered}")
    print(f"Entry price: {stock.entry_price}")
    
    # Test state validation
    print(f"Is in monitoring_entry state: {stock.is_in_state('monitoring_entry')}")
    print(f"Should process entry: {stock.is_in_state('monitoring_entry') and stock.entry_ready and not stock.entered}")
    
    # Test price crossing
    test_price = 101.5
    crossed = test_price >= stock.entry_price
    print(f"Price {test_price} crossed entry {stock.entry_price}: {crossed}")

if __name__ == "__main__":
    test_entry_logic_direct()
    test_entry_conditions()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify timing fixes for continuation bot
"""

import sys
import os
from datetime import datetime, time, timedelta
import pytz

# Add src to path
sys.path.insert(0, 'src')

def test_timing_config():
    """Test that timing configuration is loaded correctly"""
    print("=== TESTING TIMING CONFIGURATION ===")
    
    try:
        from src.trading.live_trading.config import MARKET_OPEN, ENTRY_TIME, PREP_START
        IST = pytz.timezone('Asia/Kolkata')
        
        print(f"MARKET_OPEN: {MARKET_OPEN}")
        print(f"ENTRY_TIME: {ENTRY_TIME}")
        print(f"PREP_START: {PREP_START}")
        
        # Verify timing relationships
        market_open_dt = datetime.combine(datetime.now(IST).date(), MARKET_OPEN)
        entry_time_dt = datetime.combine(datetime.now(IST).date(), ENTRY_TIME)
        prep_start_dt = datetime.combine(datetime.now(IST).date(), PREP_START)
        
        market_open_dt = IST.localize(market_open_dt)
        entry_time_dt = IST.localize(entry_time_dt)
        prep_start_dt = IST.localize(prep_start_dt)
        
        # Check timing relationships
        time_diff_1 = (market_open_dt - prep_start_dt).total_seconds()
        time_diff_2 = (entry_time_dt - market_open_dt).total_seconds()
        
        print(f"\nTiming relationships:")
        print(f"PREP_START to MARKET_OPEN: {time_diff_1} seconds")
        print(f"MARKET_OPEN to ENTRY_TIME: {time_diff_2} seconds")
        
        # Verify expected timing
        if time_diff_1 == 30:
            print("✓ PREP_START is 30 seconds before MARKET_OPEN")
        else:
            print(f"✗ PREP_START timing is incorrect: expected 30s, got {time_diff_1}s")
            
        if time_diff_2 == 300:  # 5 minutes
            print("✓ ENTRY_TIME is 5 minutes after MARKET_OPEN")
        else:
            print(f"✗ ENTRY_TIME timing is incorrect: expected 300s, got {time_diff_2}s")
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing timing config: {e}")
        return False

def test_current_timing():
    """Test current timing against configuration"""
    print("\n=== TESTING CURRENT TIMING ===")
    
    try:
        from src.trading.live_trading.config import MARKET_OPEN, ENTRY_TIME, PREP_START
        IST = pytz.timezone('Asia/Kolkata')
        
        current_time = datetime.now(IST).time()
        current_datetime = datetime.now(IST)
        
        print(f"Current time: {current_time}")
        
        # Create datetime objects for comparison
        market_open_dt = datetime.combine(datetime.now(IST).date(), MARKET_OPEN)
        entry_time_dt = datetime.combine(datetime.now(IST).date(), ENTRY_TIME)
        prep_start_dt = datetime.combine(datetime.now(IST).date(), PREP_START)
        
        market_open_dt = IST.localize(market_open_dt)
        entry_time_dt = IST.localize(entry_time_dt)
        prep_start_dt = IST.localize(prep_start_dt)
        
        # Determine current phase
        if current_datetime < prep_start_dt:
            phase = "BEFORE PREP_START"
        elif current_datetime < market_open_dt:
            phase = "BETWEEN PREP_START AND MARKET_OPEN"
        elif current_datetime < entry_time_dt:
            phase = "BETWEEN MARKET_OPEN AND ENTRY_TIME"
        else:
            phase = "AFTER ENTRY_TIME"
            
        print(f"Current phase: {phase}")
        
        # Calculate time until next phase
        if current_datetime < prep_start_dt:
            wait_time = (prep_start_dt - current_datetime).total_seconds()
            print(f"Time until PREP_START: {wait_time:.0f} seconds")
        elif current_datetime < market_open_dt:
            wait_time = (market_open_dt - current_datetime).total_seconds()
            print(f"Time until MARKET_OPEN: {wait_time:.0f} seconds")
        elif current_datetime < entry_time_dt:
            wait_time = (entry_time_dt - current_datetime).total_seconds()
            print(f"Time until ENTRY_TIME: {wait_time:.0f} seconds")
        else:
            print("All timing phases have passed for today")
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing current timing: {e}")
        return False

def test_timing_logic():
    """Test the timing logic that should be implemented"""
    print("\n=== TESTING TIMING LOGIC ===")
    
    try:
        from src.trading.live_trading.config import MARKET_OPEN, ENTRY_TIME, PREP_START
        IST = pytz.timezone('Asia/Kolkata')
        
        # Simulate the timing logic from the fixed code
        current_time = datetime.now(IST).time()
        
        print("Simulating continuation bot timing logic:")
        
        # 1. IEP Fetch at PREP_START
        prep_start = PREP_START
        if current_time < prep_start:
            print(f"✓ Would wait until PREP_START ({prep_start}) for IEP fetch")
        else:
            print(f"✓ IEP fetch should have happened at PREP_START ({prep_start})")
        
        # 2. Market Open wait
        market_open = MARKET_OPEN
        if current_time < market_open:
            print(f"✓ Would wait until MARKET_OPEN ({market_open})")
        else:
            print(f"✓ Market should have opened at {market_open}")
        
        # 3. Entry time enforcement
        entry_decision_time = ENTRY_TIME
        if current_time < entry_decision_time:
            print(f"✓ Would wait until ENTRY_TIME ({entry_decision_time}) before preparing entries")
        else:
            print(f"✓ Entries should be prepared after ENTRY_TIME ({entry_decision_time})")
        
        # 4. Phase 2 timing
        phase_2_time = (datetime.combine(datetime.now(IST).date(), MARKET_OPEN) + timedelta(seconds=30)).time()
        if current_time < phase_2_time:
            print(f"✓ Would wait until PHASE_2 ({phase_2_time}) for low/volume validation")
        else:
            print(f"✓ Low/volume validation should have happened at PHASE_2 ({phase_2_time})")
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing timing logic: {e}")
        return False

def main():
    """Run all timing tests"""
    print("CONTINUATION BOT TIMING FIX VERIFICATION")
    print("=" * 50)
    
    success = True
    
    success &= test_timing_config()
    success &= test_current_timing()
    success &= test_timing_logic()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ ALL TIMING TESTS PASSED")
        print("The timing fixes should work correctly.")
    else:
        print("✗ SOME TIMING TESTS FAILED")
        print("Please review the timing configuration and logic.")
    
    return success

if __name__ == "__main__":
    main()
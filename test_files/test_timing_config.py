#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for timing configuration and import debugging
"""

import sys
import os
import traceback

def test_imports():
    """Test all imports to find the source of the 'name a' error"""
    print("=== TESTING IMPORTS ===")
    
    # Add src to path
    sys.path.append('src/trading/live_trading')
    
    # Test each import individually
    imports_to_test = [
        ('config', 'from config import MARKET_OPEN, WINDOW_LENGTH, PREP_START, ENTRY_TIME'),
        ('StockMonitor', 'from src.trading.live_trading.continuation_stock_monitor import StockMonitor'),
        ('ReversalMonitor', 'from src.trading.live_trading.reversal_monitor import ReversalMonitor'),
        ('RuleEngine', 'from src.trading.live_trading.rule_engine import RuleEngine'),
        ('SelectionEngine', 'from src.trading.live_trading.selection_engine import SelectionEngine'),
        ('PaperTrader', 'from src.trading.live_trading.paper_trader import PaperTrader'),
        ('SimpleStockStreamer', 'from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer'),
        ('UpstoxFetcher', 'from src.utils.upstox_fetcher import UpstoxFetcher'),
    ]
    
    for name, import_statement in imports_to_test:
        try:
            exec(import_statement)
            print(f"✓ {name} import OK")
        except Exception as e:
            print(f"✗ {name} import error: {e}")
            print(f"  Full traceback:")
            traceback.print_exc()
            return False
    
    return True

def test_timing_config():
    """Test the dynamic timing configuration"""
    print("\n=== TESTING TIMING CONFIGURATION ===")
    
    try:
        from config import MARKET_OPEN, WINDOW_LENGTH, PREP_START, ENTRY_TIME
        
        print(f"MARKET_OPEN: {MARKET_OPEN}")
        print(f"WINDOW_LENGTH: {WINDOW_LENGTH} minutes")
        print(f"PREP_START: {PREP_START}")
        print(f"ENTRY_TIME: {ENTRY_TIME}")
        
        # Verify calculations
        from datetime import timedelta, datetime
        
        expected_prep_start = (datetime.combine(datetime.today(), MARKET_OPEN) - timedelta(seconds=30)).time()
        expected_entry_time = (datetime.combine(datetime.today(), MARKET_OPEN) + timedelta(minutes=WINDOW_LENGTH)).time()
        
        if PREP_START == expected_prep_start:
            print("✓ PREP_START calculation correct")
        else:
            print(f"✗ PREP_START calculation wrong: expected {expected_prep_start}, got {PREP_START}")
            
        if ENTRY_TIME == expected_entry_time:
            print("✓ ENTRY_TIME calculation correct")
        else:
            print(f"✗ ENTRY_TIME calculation wrong: expected {expected_entry_time}, got {ENTRY_TIME}")
            
        return True
        
    except Exception as e:
        print(f"✗ Timing config test error: {e}")
        traceback.print_exc()
        return False

def test_full_reversal_import():
    """Test importing the full reversal bot to catch the 'name a' error"""
    print("\n=== TESTING FULL REVERSAL BOT IMPORT ===")
    
    try:
        # Import the full reversal bot components
        sys.path.append('src/trading/live_trading')
        
        from src.trading.live_trading.reversal_stock_monitor import ReversalStockMonitor
        from src.trading.live_trading.reversal_monitor import ReversalMonitor
        from src.trading.live_trading.rule_engine import RuleEngine
        from src.trading.live_trading.selection_engine import SelectionEngine
        from src.trading.live_trading.paper_trader import PaperTrader
        from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer
        from src.utils.upstox_fetcher import UpstoxFetcher
        from config import MARKET_OPEN, ENTRY_TIME, API_POLL_DELAY_SECONDS, API_RETRY_DELAY_SECONDS
        
        print("✓ All reversal bot components imported successfully")
        return True
        
    except Exception as e:
        print(f"✗ Full reversal import error: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("TIMING CONFIGURATION AND IMPORT DEBUG TEST")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test timing config
    timing_ok = test_timing_config()
    
    # Test full reversal import
    full_import_ok = test_full_reversal_import()
    
    print("\n=== TEST SUMMARY ===")
    print(f"Imports: {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"Timing Config: {'✓ PASS' if timing_ok else '✗ FAIL'}")
    print(f"Full Import: {'✓ PASS' if full_import_ok else '✗ FAIL'}")
    
    if imports_ok and timing_ok and full_import_ok:
        print("\n🎉 ALL TESTS PASSED! The reversal bot should work correctly.")
    else:
        print("\n❌ SOME TESTS FAILED! Need to fix the issues above.")
    
    return imports_ok and timing_ok and full_import_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
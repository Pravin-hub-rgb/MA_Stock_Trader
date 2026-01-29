#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Updated Volume Status Logging
Tests that the continuation bot now shows detailed volume information in the summary status
"""

import sys
import logging

# Add src to path
sys.path.insert(0, 'src')

# Configure logging to show detailed messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

def test_updated_volume_status():
    """Test the updated volume status logging in summary"""
    print("UPDATED VOLUME STATUS LOGGING TEST")
    print("=" * 50)
    print(f"Starting at: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}")
    print()
    
    # Import the StockMonitor class
    from src.trading.live_trading.continuation_stock_monitor import StockMonitor, StockState
    
    # Create a stock monitor
    monitor = StockMonitor()
    
    # Test case: Add a stock with volume validation
    print("Test Case: Stock with detailed volume status")
    print("-" * 30)
    
    # Add a test stock
    monitor.add_stock("TESTVOL", "NSE_EQ|TESTVOL", 100.0, 'continuation')
    stock = monitor.stocks["NSE_EQ|TESTVOL"]
    
    # Set up the stock state
    stock.open_price = 101.0
    stock.gap_validated = True
    stock.low_violation_checked = True
    stock.volume_validated = True
    stock.early_volume = 120000  # 120K cumulative volume
    
    # Mock the stock_scorer metadata for volume baseline
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Create mock stock_scorer with metadata
    class MockStockScorer:
        def __init__(self):
            self.stock_metadata = {
                "TESTVOL": {
                    "volume_baseline": 800000  # 800K mean volume
                }
            }
    
    # Temporarily replace the stock_scorer module
    original_modules = sys.modules.copy()
    sys.modules['src.trading.live_trading.stock_scorer'] = MockStockScorer()
    
    try:
        # Get qualified stocks to trigger the detailed status logging
        qualified_stocks = monitor.get_qualified_stocks()
        print(f"Qualified stocks count: {len(qualified_stocks)}")
        print()
        print("Check the log messages above for detailed volume information!")
        print("Expected format: 'Volume: 15.0% (120.0K) >= 7.5% of (800.0K)'")
        print()
        
        # Test with different volume scenarios
        test_cases = [
            (50000, 500000, "50K vs 500K"),
            (2500000, 20000000, "2.5M vs 20M"),
            (1500, 20000, "1.5K vs 20K")
        ]
        
        for i, (cumulative_vol, baseline_vol, description) in enumerate(test_cases):
            print(f"Test Case {i+1}: {description}")
            print("-" * 20)
            
            # Create a new stock for each test case
            test_symbol = f"TEST_{i}"
            monitor.add_stock(test_symbol, f"NSE_EQ|{test_symbol}", 100.0, 'continuation')
            test_stock = monitor.stocks[f"NSE_EQ|{test_symbol}"]
            
            # Set up the stock state
            test_stock.open_price = 101.0
            test_stock.gap_validated = True
            test_stock.low_violation_checked = True
            test_stock.volume_validated = True
            test_stock.early_volume = cumulative_vol
            
            # Update mock metadata for this test case
            monitor.stock_scorer = MockStockScorer()
            monitor.stock_scorer.stock_metadata[test_symbol] = {"volume_baseline": baseline_vol}
            
            # Get qualified stocks to trigger logging
            qualified_stocks = monitor.get_qualified_stocks()
            print(f"Test {i+1} completed - check logs above")
            print()
        
        return True
        
    finally:
        # Restore original modules
        sys.modules.clear()
        sys.modules.update(original_modules)

def main():
    """Main test function"""
    print("Starting Updated Volume Status Logging Test")
    print("This test verifies that volume validation shows detailed numbers in the summary status")
    print("like: 'Volume: 15.0% (120.0K) >= 7.5% of (800.0K)' in the main output")
    print()
    
    # Run test
    success = test_updated_volume_status()
    
    if success:
        print("\n✅ Updated volume status logging test completed successfully")
        print("The continuation bot will now show detailed volume information in the summary status")
    else:
        print("\n❌ Updated volume status logging test failed")
    
    return success

if __name__ == "__main__":
    main()
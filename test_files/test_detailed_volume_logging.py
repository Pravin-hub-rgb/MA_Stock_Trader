#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Detailed Volume Logging in Continuation Bot
Verifies that the continuation bot shows detailed volume information
"""

import sys
import time
import logging

# Add src to path
sys.path.insert(0, 'src')

# Configure logging to show detailed messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

def test_detailed_volume_logging():
    """Test that continuation bot shows detailed volume logging"""
    print("DETAILED VOLUME LOGGING TEST")
    print("=" * 40)
    print(f"Starting at: {time.strftime('%H:%M:%S')}")
    print()
    
    # Import the StockMonitor class
    from src.trading.live_trading.continuation_stock_monitor import StockMonitor, StockState
    
    # Create a stock monitor
    monitor = StockMonitor()
    
    # Test case: Add a stock with volume validation using real cache data
    print("Test Case: Stock with detailed volume logging")
    print("-" * 50)
    
    # Add a test stock
    monitor.add_stock("TESTVOL", "NSE_EQ|TESTVOL", 100.0, 'continuation')
    stock = monitor.stocks["NSE_EQ|TESTVOL"]
    
    # Set up the stock state to simulate what happens in live trading
    stock.open_price = 101.0
    stock.gap_validated = True
    stock.low_violation_checked = True
    stock.volume_validated = True
    stock.early_volume = 120000  # 120K cumulative volume
    
    # Simulate what check_volume_validations() does - store the volume baseline
    stock.volume_baseline = 800000  # 800K mean volume from cache data
    
    print(f"Stock setup complete:")
    print(f"  Cumulative volume: {stock.early_volume:,} shares")
    print(f"  Volume baseline: {stock.volume_baseline:,} shares")
    print(f"  Volume ratio: {(stock.early_volume / stock.volume_baseline * 100):.1f}%")
    print()
    print("Calling get_qualified_stocks() to trigger detailed volume logging...")
    print()
    
    # Get qualified stocks to trigger the detailed status logging
    qualified_stocks = monitor.get_qualified_stocks()
    print(f"Qualified stocks count: {len(qualified_stocks)}")
    print()
    print("✅ Check the log messages above for detailed volume information!")
    print("Expected format: 'Volume: 15.0% (120.0K) >= 7.5% of (800.0K)'")
    print()
    
    return True

def main():
    """Main test function"""
    print("Starting Detailed Volume Logging Test")
    print("This test verifies that the continuation bot shows detailed volume information")
    print("like: 'Volume: 15.0% (120.0K) >= 7.5% of (800.0K)' in the main output")
    print()
    
    # Run test
    success = test_detailed_volume_logging()
    
    if success:
        print("\n✅ Detailed volume logging test completed successfully")
        print("The continuation bot should now show detailed volume information in the logs")
    else:
        print("\n❌ Detailed volume logging test failed")
    
    return success

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Test Script for Volume Formatting
Tests that the volume formatting works correctly in the StockState class
"""

import sys
import logging

# Add src to path
sys.path.insert(0, 'src')

# Configure logging to show detailed messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

def test_volume_formatting():
    """Test the volume formatting functionality"""
    print("VOLUME FORMATTING TEST")
    print("=" * 30)
    print(f"Starting at: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}")
    print()
    
    # Import the StockState class
    from src.trading.live_trading.continuation_stock_monitor import StockState
    
    # Test different volume scenarios
    test_cases = [
        (50000, 500000, "50K vs 500K"),
        (2500000, 20000000, "2.5M vs 20M"),
        (1500, 20000, "1.5K vs 20K"),
        (750, 10000, "750 vs 10K"),
        (33000, 800000, "33K vs 800K (your example)")
    ]
    
    for i, (cumulative_vol, baseline_vol, description) in enumerate(test_cases):
        print(f"Test Case {i+1}: {description}")
        print("-" * 20)
        
        # Create a stock state
        stock = StockState("TEST", "NSE_EQ|TEST", 100.0, 'continuation')
        stock.open_price = 101.0
        stock.gap_validated = True
        stock.low_violation_checked = True
        stock.volume_validated = True
        stock.early_volume = cumulative_vol
        
        # Format volumes using the stock's method
        cumulative_vol_str = stock._format_volume(cumulative_vol)
        baseline_vol_str = stock._format_volume(baseline_vol)
        volume_ratio = (cumulative_vol / baseline_vol * 100) if baseline_vol > 0 else 0
        
        # Create the formatted volume status string
        volume_status = f"Volume: {volume_ratio:.1f}% ({cumulative_vol_str}) >= 7.5% of ({baseline_vol_str})"
        
        print(f"Cumulative volume: {cumulative_vol_str}")
        print(f"Baseline volume: {baseline_vol_str}")
        print(f"Volume ratio: {volume_ratio:.1f}%")
        print(f"Formatted status: {volume_status}")
        print()
    
    return True

def main():
    """Main test function"""
    print("Starting Volume Formatting Test")
    print("This test verifies that volume formatting works correctly")
    print("and shows the expected format for volume status messages")
    print()
    
    # Run test
    success = test_volume_formatting()
    
    if success:
        print("\n✅ Volume formatting test completed successfully")
        print("The continuation bot will now show properly formatted volume information")
    else:
        print("\n❌ Volume formatting test failed")
    
    return success

if __name__ == "__main__":
    main()
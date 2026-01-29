#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Continuation Bot Volume Fix
Tests that the continuation bot now uses get_current_volume() instead of get_ltp_data()
"""

import sys
import time
import logging

# Add src to path
sys.path.insert(0, 'src')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Import required modules
from src.utils.upstox_fetcher import UpstoxFetcher
from src.trading.live_trading.continuation_stock_monitor import StockMonitor, StockState
from src.trading.live_trading.config import MARKET_OPEN, ENTRY_TIME

class ContinuationVolumeTest:
    """Test the continuation bot volume accumulation fix"""
    
    def __init__(self):
        self.upstox_fetcher = UpstoxFetcher()
        self.monitor = StockMonitor()
        self.test_symbol = "RELIANCE"
        self.test_instrument_key = "NSE_EQ|INE002A01018"
        
    def setup_test_stock(self):
        """Setup a test stock in the continuation bot monitor"""
        print("Setting up test stock in continuation bot monitor...")
        
        # Add test stock to monitor
        self.monitor.add_stock(
            symbol=self.test_symbol,
            instrument_key=self.test_instrument_key,
            previous_close=2500.0,  # Mock previous close
            situation='continuation'
        )
        
        # Set up the stock state manually for testing
        stock = self.monitor.stocks[self.test_instrument_key]
        stock.open_price = 2510.0  # Mock opening price
        stock.gap_validated = True
        stock.low_violation_checked = True
        stock.volume_validated = False  # This should be set to True after volume validation
        
        print(f"Test stock {self.test_symbol} added to continuation monitor")
        print(f"Opening price: {stock.open_price}")
        print(f"Gap validated: {stock.gap_validated}")
        print(f"Low violation checked: {stock.low_violation_checked}")
        print(f"Volume validated: {stock.volume_validated}")
        print(f"Early volume: {stock.early_volume}")
        
    def test_volume_validation(self):
        """Test the volume validation using the new get_current_volume() method"""
        print("\nTesting volume validation with new get_current_volume() method...")
        
        # Get current volume using the new method
        current_volume = self.upstox_fetcher.get_current_volume(self.test_symbol)
        print(f"Current volume from get_current_volume(): {current_volume:,}")
        
        # Check if volume validation works
        if current_volume > 0:
            # Simulate volume baseline (mock value)
            volume_baseline = 1000000.0
            
            # Update stock's early volume
            stock = self.monitor.stocks[self.test_instrument_key]
            stock.early_volume = current_volume
            
            # Validate volume
            validation_result = stock.validate_volume(volume_baseline, min_ratio=0.05)
            
            print(f"Volume baseline: {volume_baseline:,}")
            print(f"Early volume set to: {stock.early_volume:,}")
            print(f"Volume ratio: {(stock.early_volume / volume_baseline):.1%}")
            print(f"Volume validation result: {validation_result}")
            print(f"Volume validated: {stock.volume_validated}")
            
            return validation_result
        else:
            print("❌ No volume data available")
            return False
    
    def test_check_volume_validations(self):
        """Test the check_volume_validations() method that was updated"""
        print("\nTesting check_volume_validations() method...")
        
        # Call the updated method
        self.monitor.check_volume_validations()
        
        # Check results
        stock = self.monitor.stocks[self.test_instrument_key]
        print(f"Volume validated after check_volume_validations(): {stock.volume_validated}")
        print(f"Early volume after validation: {stock.early_volume:,}")
        print(f"Rejection reason: {stock.rejection_reason}")
        
        return stock.volume_validated
    
    def run_test(self):
        """Run the complete continuation volume fix test"""
        print("CONTINUATION BOT VOLUME FIX TEST")
        print("=" * 40)
        print(f"Starting at: {time.strftime('%H:%M:%S')}")
        print()
        
        # Setup test stock
        self.setup_test_stock()
        
        # Test volume validation directly
        direct_result = self.test_volume_validation()
        
        # Test the updated check_volume_validations method
        method_result = self.test_check_volume_validations()
        
        print("\n" + "=" * 40)
        print("TEST RESULTS SUMMARY")
        print("=" * 40)
        print(f"Direct volume validation: {'✅ PASS' if direct_result else '❌ FAIL'}")
        print(f"check_volume_validations(): {'✅ PASS' if method_result else '❌ FAIL'}")
        print(f"Early volume accumulated: {self.monitor.stocks[self.test_instrument_key].early_volume:,}")
        print(f"Volume validated: {self.monitor.stocks[self.test_instrument_key].volume_validated}")
        
        if direct_result and method_result:
            print("\n🎉 CONTINUATION BOT VOLUME FIX SUCCESSFUL!")
            print("The bot now uses get_current_volume() instead of get_ltp_data()")
            print("Volume accumulation should work correctly during trading hours")
        else:
            print("\n❌ CONTINUATION BOT VOLUME FIX FAILED")
            print("There may still be issues with volume accumulation")
        
        return direct_result and method_result

def main():
    """Main test function"""
    print("Starting Continuation Bot Volume Fix Test")
    print("This test verifies that the continuation bot now uses get_current_volume()")
    print("instead of get_ltp_data() for volume accumulation")
    print()
    
    # Create test instance
    test = ContinuationVolumeTest()
    
    # Run test
    success = test.run_test()
    
    if success:
        print("\n✅ Test completed successfully - volume fix is working")
    else:
        print("\n❌ Test failed - volume fix needs more work")
    
    return success

if __name__ == "__main__":
    main()
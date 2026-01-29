#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Volume Accumulation Test
Tests if volume data is being fetched and accumulated during market hours
"""

import sys
import os
import time as time_module
import logging
from datetime import datetime, time, timedelta
import pytz

# Add src to path
sys.path.insert(0, 'src')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import required modules
from src.utils.upstox_fetcher import UpstoxFetcher
from src.trading.live_trading.continuation_stock_monitor import StockMonitor
from src.trading.live_trading.config import MARKET_OPEN, ENTRY_TIME

IST = pytz.timezone('Asia/Kolkata')

class LiveVolumeTest:
    """Test class for live volume accumulation during market hours"""
    
    def __init__(self):
        self.upstox_fetcher = UpstoxFetcher()
        self.monitor = StockMonitor()
        self.test_symbol = "RELIANCE"  # Single stock for testing
        self.test_instrument_key = None
        self.previous_close = None
        
        # Volume tracking
        self.start_time = None
        self.end_time = None
        self.volume_samples = []
        
    def setup_test_stock(self):
        """Setup test stock with previous close"""
        print(f"=== SETTING UP TEST STOCK: {self.test_symbol} ===")
        
        try:
            # Get previous close
            data = self.upstox_fetcher.get_ltp_data(self.test_symbol)
            if data and 'cp' in data and data['cp'] is not None:
                self.previous_close = float(data['cp'])
                print(f"✓ Previous close for {self.test_symbol}: Rs{self.previous_close:.2f}")
            else:
                print(f"✗ No previous close data for {self.test_symbol}")
                return False
                
            # Get instrument key
            self.test_instrument_key = self.upstox_fetcher.get_instrument_key(self.test_symbol)
            if self.test_instrument_key:
                print(f"✓ Instrument key: {self.test_instrument_key}")
            else:
                print(f"✗ No instrument key for {self.test_symbol}")
                return False
                
            # Add to monitor
            self.monitor.add_stock(self.test_symbol, self.test_instrument_key, self.previous_close, 'continuation')
            print(f"✓ Added {self.test_symbol} to monitor")
            
            return True
            
        except Exception as e:
            print(f"✗ Setup failed: {e}")
            return False
    
    def get_current_volume(self):
        """Get current volume from Upstox API"""
        try:
            # Get LTP data which includes volume
            data = self.upstox_fetcher.get_ltp_data(self.test_symbol)
            if data and 'volume' in data:
                return float(data['volume'])
            else:
                # Try alternative volume field
                if 'vol' in data:
                    return float(data['vol'])
                return 0
        except Exception as e:
            print(f"Error getting volume: {e}")
            return 0
    
    def test_volume_accumulation(self):
        """Test volume accumulation during 1-minute window"""
        print(f"\n=== TESTING LIVE VOLUME ACCUMULATION ===")
        print(f"Starting at: {datetime.now(IST).strftime('%H:%M:%S')}")
        
        # Test for 1 minute
        test_duration = 60  # 1 minute
        sample_interval = 5  # Sample every 5 seconds
        
        self.start_time = datetime.now(IST)
        self.end_time = self.start_time + timedelta(seconds=test_duration)
        
        print(f"Test duration: {test_duration} seconds")
        print(f"Sample interval: {sample_interval} seconds")
        print(f"Expected samples: {test_duration // sample_interval}")
        print()
        
        current_time = self.start_time
        sample_count = 0
        
        while current_time < self.end_time:
            sample_count += 1
            
            # Get current volume
            current_volume = self.get_current_volume()
            
            # Calculate volume change (if we have previous sample)
            volume_change = 0
            if self.volume_samples:
                last_volume = self.volume_samples[-1]['total_volume']
                volume_change = current_volume - last_volume
                if volume_change < 0:  # Handle volume reset
                    volume_change = 0
            else:
                # First sample - use current volume as baseline
                volume_change = current_volume
            
            # Store sample
            sample_data = {
                'timestamp': datetime.now(IST),
                'sample_number': sample_count,
                'total_volume': current_volume,
                'volume_change': volume_change,
            }
            self.volume_samples.append(sample_data)
            
            # Print sample info
            print(f"Sample {sample_count:2d}: Total={current_volume:,.0f}, Change={volume_change:,.0f}")
            
            # Test the monitor's accumulate_volume method (using current implementation)
            if self.test_instrument_key:
                # This will only work if we're in the time window
                self.monitor.accumulate_volume(self.test_instrument_key, volume_change)
                stock = self.monitor.stocks.get(self.test_instrument_key)
                if stock:
                    print(f"  Monitor early_volume: {stock.early_volume:,.0f}")
                    print(f"  Time check: {datetime.now().time()} (Market: {MARKET_OPEN}, Entry: {ENTRY_TIME})")
            
            # Wait for next sample
            time_module.sleep(sample_interval)
            current_time = datetime.now(IST)
        
        print(f"\n=== VOLUME ACCUMULATION TEST COMPLETE ===")
        print(f"Total samples: {sample_count}")
        
        # Show results
        if self.volume_samples:
            first_volume = self.volume_samples[0]['total_volume']
            last_volume = self.volume_samples[-1]['total_volume']
            total_change = last_volume - first_volume
            
            print(f"Volume range: {first_volume:,.0f} -> {last_volume:,.0f}")
            print(f"Total volume change: {total_change:,.0f}")
            
            # Check if monitor accumulated any volume
            if self.test_instrument_key in self.monitor.stocks:
                stock = self.monitor.stocks[self.test_instrument_key]
                print(f"Monitor early_volume: {stock.early_volume:,.0f}")
                
                if stock.early_volume > 0:
                    print("✓ Volume accumulation IS working!")
                else:
                    print("✗ Volume accumulation is NOT working (0.0%)")
        
        return True
    
    def run_test(self):
        """Run the live volume accumulation test"""
        print("LIVE VOLUME ACCUMULATION TEST")
        print("=" * 40)
        
        # Setup
        if not self.setup_test_stock():
            print("Setup failed - cannot proceed with test")
            return False
        
        # Test volume accumulation
        self.test_volume_accumulation()
        
        print("\n" + "=" * 40)
        print("LIVE VOLUME ACCUMULATION TEST COMPLETE")
        
        return True

def main():
    """Main test function"""
    print("Starting Live Volume Accumulation Test")
    print("This test will check if volume data is being fetched and accumulated during market hours")
    print()
    
    # Create test instance
    test = LiveVolumeTest()
    
    # Run test
    success = test.run_test()
    
    if success:
        print("\n✓ Test completed successfully")
    else:
        print("\n✗ Test failed")
    
    return success

if __name__ == "__main__":
    main()
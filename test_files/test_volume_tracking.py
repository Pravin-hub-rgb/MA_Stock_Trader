#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Volume Tracking Test Script
Tests live volume accumulation for SVRO relative volume calculation
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

class VolumeTrackingTest:
    """Test class for volume tracking functionality"""
    
    def __init__(self):
        self.upstox_fetcher = UpstoxFetcher()
        self.monitor = StockMonitor()
        self.test_symbol = "RELIANCE"  # Single stock for testing
        self.test_instrument_key = None
        self.previous_close = None
        
        # Volume tracking variables
        self.start_time = None
        self.end_time = None
        self.volume_samples = []
        self.cumulative_volume = 0
        
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
    
    def simulate_volume_accumulation(self):
        """Simulate volume accumulation over time"""
        print(f"\n=== SIMULATING VOLUME ACCUMULATION ===")
        print(f"Starting at: {datetime.now(IST).strftime('%H:%M:%S')}")
        
        # Simulate 5-minute window (300 seconds)
        test_duration = 300  # 5 minutes
        sample_interval = 10  # Sample every 10 seconds
        
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
            
            self.cumulative_volume += volume_change
            
            # Store sample
            sample_data = {
                'timestamp': datetime.now(IST),
                'sample_number': sample_count,
                'total_volume': current_volume,
                'volume_change': volume_change,
                'cumulative_volume': self.cumulative_volume
            }
            self.volume_samples.append(sample_data)
            
            # Print sample info
            print(f"Sample {sample_count:2d}: Total={current_volume:,.0f}, Change={volume_change:,.0f}, Cumulative={self.cumulative_volume:,.0f}")
            
            # Test the monitor's accumulate_volume method with force parameter
            if self.test_instrument_key:
                self.monitor.accumulate_volume(self.test_instrument_key, volume_change, force_accumulate=True)
                stock = self.monitor.stocks.get(self.test_instrument_key)
                if stock:
                    print(f"  Monitor early_volume: {stock.early_volume:,.0f}")
            
            # Wait for next sample
            time_module.sleep(sample_interval)
            current_time = datetime.now(IST)
        
        print(f"\n=== VOLUME ACCUMULATION COMPLETE ===")
        print(f"Total samples: {sample_count}")
        print(f"Final cumulative volume: {self.cumulative_volume:,.0f}")
        
        # Show volume baseline calculation
        self.test_volume_baseline()
        
        return True
    
    def test_volume_baseline(self):
        """Test volume baseline calculation"""
        print(f"\n=== TESTING VOLUME BASELINE CALCULATION ===")
        
        try:
            # Import stock scorer to test baseline calculation
            from src.trading.live_trading.stock_scorer import stock_scorer
            
            # Preload metadata for our test stock
            stock_scorer.preload_metadata([self.test_symbol], {self.test_symbol: self.previous_close})
            
            if self.test_symbol in stock_scorer.stock_metadata:
                metadata = stock_scorer.stock_metadata[self.test_symbol]
                volume_baseline = metadata['volume_baseline']
                print(f"✓ Volume baseline for {self.test_symbol}: {volume_baseline:,.0f}")
                
                # Calculate relative volume
                if volume_baseline > 0:
                    relative_volume = self.cumulative_volume / volume_baseline
                    print(f"✓ Relative volume: {relative_volume:.3f} ({relative_volume*100:.1f}%)")
                    
                    # Test SVRO validation
                    from src.trading.live_trading.config import SVRO_MIN_VOLUME_RATIO
                    print(f"✓ SVRO threshold: {SVRO_MIN_VOLUME_RATIO*100:.1f}%")
                    
                    if relative_volume >= SVRO_MIN_VOLUME_RATIO:
                        print(f"✓ PASS: Volume validation would succeed")
                    else:
                        print(f"✗ FAIL: Volume validation would fail - {relative_volume*100:.1f}% < {SVRO_MIN_VOLUME_RATIO*100:.1f}%")
                else:
                    print(f"✗ Volume baseline is zero or invalid")
            else:
                print(f"✗ Could not get metadata for {self.test_symbol}")
                
        except Exception as e:
            print(f"✗ Volume baseline test failed: {e}")
    
    def test_volume_tracking_integration(self):
        """Test volume tracking integration with stock monitor"""
        print(f"\n=== TESTING VOLUME TRACKING INTEGRATION ===")
        
        # Test the stock monitor's volume tracking
        if self.test_instrument_key in self.monitor.stocks:
            stock = self.monitor.stocks[self.test_instrument_key]
            
            print(f"Stock state before test:")
            print(f"  early_volume: {stock.early_volume}")
            print(f"  volume_validated: {stock.volume_validated}")
            
            # Test manual volume accumulation
            test_volume = 100000
            self.monitor.accumulate_volume(self.test_instrument_key, test_volume)
            print(f"After adding {test_volume:,}: early_volume = {stock.early_volume}")
            
            # Test volume validation
            try:
                from src.trading.live_trading.stock_scorer import stock_scorer
                if self.test_symbol in stock_scorer.stock_metadata:
                    metadata = stock_scorer.stock_metadata[self.test_symbol]
                    volume_baseline = metadata['volume_baseline']
                    
                    validation_result = stock.validate_volume(volume_baseline, 0.05)
                    print(f"Volume validation result: {validation_result}")
                    print(f"  volume_validated: {stock.volume_validated}")
                    print(f"  rejection_reason: {stock.rejection_reason}")
                else:
                    print("Cannot test validation - no metadata available")
            except Exception as e:
                print(f"Volume validation test failed: {e}")
    
    def run_full_test(self):
        """Run complete volume tracking test"""
        print("VOLUME TRACKING TEST START")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_stock():
            print("Setup failed - cannot proceed with test")
            return False
        
        # Test volume accumulation
        self.simulate_volume_accumulation()
        
        # Test integration
        self.test_volume_tracking_integration()
        
        print("\n" + "=" * 50)
        print("VOLUME TRACKING TEST COMPLETE")
        
        # Summary
        print(f"\nSUMMARY:")
        print(f"  Test stock: {self.test_symbol}")
        print(f"  Previous close: Rs{self.previous_close:.2f}")
        print(f"  Cumulative volume: {self.cumulative_volume:,.0f}")
        print(f"  Samples taken: {len(self.volume_samples)}")
        
        if self.volume_samples:
            print(f"  Volume range: {self.volume_samples[0]['total_volume']:,.0f} -> {self.volume_samples[-1]['total_volume']:,.0f}")
        
        return True

def main():
    """Main test function"""
    print("Starting Volume Tracking Test")
    print("This test will verify volume accumulation for SVRO relative volume calculation")
    print()
    
    # Create test instance
    test = VolumeTrackingTest()
    
    # Run test
    success = test.run_full_test()
    
    if success:
        print("\n✓ Test completed successfully")
    else:
        print("\n✗ Test failed")
    
    return success

if __name__ == "__main__":
    main()
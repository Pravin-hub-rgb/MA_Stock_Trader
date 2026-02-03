#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Volume Accumulation Test
Tests volume fetching and accumulation for 1 minute starting now
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

class SimpleVolumeTest:
    """Simple test for volume accumulation"""
    
    def __init__(self):
        self.upstox_fetcher = UpstoxFetcher()
        self.test_symbol = "RELIANCE"
        
    def get_current_volume(self):
        """Get current volume from Upstox API"""
        try:
            data = self.upstox_fetcher.get_ltp_data(self.test_symbol)
            if data and 'volume' in data:
                return float(data['volume'])
            elif data and 'vol' in data:
                return float(data['vol'])
            return 0
        except Exception as e:
            print(f"Error getting volume: {e}")
            return 0
    
    def run_test(self):
        """Run simple volume accumulation test for 1 minute"""
        print("SIMPLE VOLUME ACCUMULATION TEST")
        print("=" * 40)
        print(f"Starting at: {time.strftime('%H:%M:%S')}")
        print(f"Testing for 1 minute...")
        print()
        
        # Get initial volume
        initial_volume = self.get_current_volume()
        if initial_volume == 0:
            print("❌ Failed to get initial volume")
            return False
            
        print(f"Initial volume: {initial_volume:,}")
        
        # Test for 1 minute
        test_duration = 60  # 1 minute
        sample_interval = 5  # Sample every 5 seconds
        cumulative_volume = 0
        sample_count = 0
        
        print(f"\nSampling every {sample_interval} seconds for {test_duration} seconds:")
        print("-" * 50)
        
        start_time = time.time()
        
        while time.time() - start_time < test_duration:
            sample_count += 1
            
            # Get current volume
            current_volume = self.get_current_volume()
            
            # Calculate volume change
            volume_change = current_volume - initial_volume
            if volume_change < 0:  # Handle volume reset
                volume_change = 0
            
            # Update cumulative volume
            cumulative_volume += volume_change
            
            # Log results
            print(f"Sample {sample_count:2d}: Current={current_volume:,}, Change={volume_change:,}, Cumulative={cumulative_volume:,}")
            
            # Wait for next sample
            time.sleep(sample_interval)
        
        print("-" * 50)
        print(f"Test completed at: {time.strftime('%H:%M:%S')}")
        print(f"Total samples: {sample_count}")
        print(f"Final cumulative volume: {cumulative_volume:,}")
        
        if cumulative_volume > 0:
            print("✅ Volume accumulation IS working!")
        else:
            print("❌ Volume accumulation is NOT working (0.0%)")
        
        return True

def main():
    """Main test function"""
    print("Starting Simple Volume Accumulation Test")
    print("This test will track volume accumulation for 1 minute")
    print()
    
    # Create test instance
    test = SimpleVolumeTest()
    
    # Run test
    success = test.run_test()
    
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
    
    return success

if __name__ == "__main__":
    main()
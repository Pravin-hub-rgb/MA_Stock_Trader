#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal Volume Accumulation Test
Tests volume fetching and accumulation without historical data
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

class MinimalVolumeTest:
    """Minimal test for volume accumulation"""
    
    def __init__(self):
        self.upstox_fetcher = UpstoxFetcher()
        self.test_symbol = "RELIANCE"
        
    def get_current_volume_simple(self):
        """Get current volume using the new dedicated volume-only function"""
        try:
            # Use the new get_current_volume() function that avoids historical data
            return self.upstox_fetcher.get_current_volume(self.test_symbol)
        except Exception as e:
            print(f"Error getting volume: {e}")
            return 0
    
    def run_test(self):
        """Run minimal volume accumulation test for 1 minute"""
        print("MINIMAL VOLUME ACCUMULATION TEST")
        print("=" * 40)
        print(f"Starting at: {time.strftime('%H:%M:%S')}")
        print(f"Testing for 1 minute...")
        print()
        
        # Get initial volume
        initial_volume = self.get_current_volume_simple()
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
            current_volume = self.get_current_volume_simple()
            
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
    print("Starting Minimal Volume Accumulation Test")
    print("This test will track volume accumulation for 1 minute")
    print("No historical data fetching - just current volume")
    print()
    
    # Create test instance
    test = MinimalVolumeTest()
    
    # Run test
    success = test.run_test()
    
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
    
    return success

if __name__ == "__main__":
    main()
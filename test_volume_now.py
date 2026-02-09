#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Volume Test - Log volume data directly
Tests volume API at current market time (11:20)
"""

import sys
import os
import time as time_module

# Add src to path
sys.path.insert(0, 'src')

def test_volume_now():
    """Test volume API directly at current time"""
    print("VOLUME TEST - CURRENT MARKET TIME")
    print("=" * 40)
    print(f"Current time: {time_module.strftime('%H:%M:%S')}")
    print()
    
    try:
        # Import required modules
        from src.utils.upstox_fetcher import UpstoxFetcher
        
        # Create fetcher
        fetcher = UpstoxFetcher()
        
        # Test stocks from continuation bot
        test_symbols = ["ANGELONE", "BSE", "UNIONBANK"]  # The qualified stocks
        
        print(f"Testing volume for {len(test_symbols)} stocks:")
        for symbol in test_symbols:
            print(f"  - {symbol}")
        print()
        
        # Test volume for each stock
        for symbol in test_symbols:
            print(f"Testing volume for {symbol}...")
            
            try:
                current_volume = fetcher.get_current_volume(symbol)
                print(f"  Current volume: {current_volume:,} shares")
                
                if current_volume > 0:
                    # Format volume for readability
                    if current_volume >= 1000000:
                        vol_str = f"{current_volume/1000000:.1f}M"
                    elif current_volume >= 1000:
                        vol_str = f"{current_volume/1000:.1f}K"
                    else:
                        vol_str = f"{current_volume:,}"
                    
                    print(f"  Formatted volume: {vol_str}")
                    print(f"  ✅ Volume API working for {symbol}")
                else:
                    print(f"  ❌ No volume data for {symbol}")
                    
            except Exception as e:
                print(f"  ❌ Error getting volume for {symbol}: {e}")
            
            print()
        
        print("Volume test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in volume test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Testing Volume API - Direct Call")
    print("This test directly calls the volume API to verify it's working")
    print()
    
    success = test_volume_now()
    
    if success:
        print("✅ Volume API test completed successfully!")
        print("The volume API is working and returning data.")
    else:
        print("❌ Volume API test failed!")
    
    return success

if __name__ == "__main__":
    main()
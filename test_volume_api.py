#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Volume API Test
Tests the get_current_volume method directly
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, 'src')

def test_volume_api():
    """Test volume API directly"""
    print("VOLUME API TEST")
    print("=" * 30)
    
    try:
        # Import UpstoxFetcher
        from src.utils.upstox_fetcher import UpstoxFetcher
        
        # Create fetcher instance
        fetcher = UpstoxFetcher()
        
        # Test symbol
        symbol = "RELIANCE"
        
        print(f"Testing volume API for {symbol}")
        print(f"Starting at: {time.strftime('%H:%M:%S')}")
        print()
        
        # Get current volume
        volume = fetcher.get_current_volume(symbol)
        
        print(f"Volume result: {volume}")
        
        if volume > 0:
            print("✅ Volume API is working!")
            print(f"Current volume: {volume:,} shares")
        else:
            print("❌ Volume API returned 0 or failed")
            
        return volume > 0
        
    except Exception as e:
        print(f"❌ Error testing volume API: {e}")
        return False

if __name__ == "__main__":
    success = test_volume_api()
    if success:
        print("\n✅ Volume API test passed")
    else:
        print("\n❌ Volume API test failed")
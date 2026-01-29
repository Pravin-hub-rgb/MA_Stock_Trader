#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test UpstoxFetcher Integration
Tests the new get_opening_price method in the UpstoxFetcher class
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def test_upstox_fetcher_integration():
    """Test the UpstoxFetcher integration with the new get_opening_price method"""
    print("=" * 60)
    print("🧪 UPSTOX FETCHER INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Import the UpstoxFetcher
        from src.utils.upstox_fetcher import upstox_fetcher
        
        print("✅ UpstoxFetcher imported successfully")
        print(f"✅ Access token loaded: {'Yes' if upstox_fetcher.access_token else 'No'}")
        
        if not upstox_fetcher.access_token:
            print("❌ No access token available - skipping test")
            return
        
        # Test with RELIANCE
        test_symbol = "RELIANCE"
        print(f"🎯 Testing get_opening_price for {test_symbol}")
        print()
        
        # Call the new method
        opening_price = upstox_fetcher.get_opening_price(test_symbol)
        
        if opening_price:
            print(f"✅ SUCCESS: Got opening price for {test_symbol}: ₹{opening_price:.2f}")
        else:
            print(f"❌ FAILED: No opening price received for {test_symbol}")
            
        # Test instrument key mapping
        instrument_key = upstox_fetcher.get_instrument_key(test_symbol)
        print(f"🔍 Instrument key for {test_symbol}: {instrument_key}")
        
        print()
        print("=" * 60)
        print("🏁 INTEGRATION TEST COMPLETED")
        print("=" * 60)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_upstox_fetcher_integration()
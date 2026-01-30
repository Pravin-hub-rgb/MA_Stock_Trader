#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Connection Fix
Diagnoses and fixes WebSocket connection issues preventing tick reception
"""

import sys
import os
import time
from datetime import datetime
import pytz

# Add src to path
sys.path.insert(0, 'src')

# Import components
from src.utils.upstox_fetcher import UpstoxFetcher
from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer

def diagnose_websocket_issues():
    """Diagnose WebSocket connection issues"""
    
    print("=== WEBSOCKET CONNECTION DIAGNOSIS ===")
    print("Checking WebSocket connection issues that prevent tick reception")
    print()
    
    # Test 1: Check Upstox authentication
    print("=== TEST 1: UPSTOX AUTHENTICATION ===")
    upstox_fetcher = UpstoxFetcher()
    
    try:
        # Test token status
        print("Checking token status...")
        token_info = upstox_fetcher.get_token_status()
        print(f"Token status: {token_info}")
        
        # Test API access
        print("Testing API access...")
        test_data = upstox_fetcher.get_ltp_data("RELIANCE")
        if test_data:
            print(f"✅ API access working - got data for RELIANCE")
            print(f"   LTP: {test_data.get('ltp', 'N/A')}")
            print(f"   Previous Close: {test_data.get('cp', 'N/A')}")
        else:
            print("❌ API access failed")
            
    except Exception as e:
        print(f"❌ Authentication/API test failed: {e}")
    
    print()
    
    # Test 2: Check WebSocket connection
    print("=== TEST 2: WEBSOCKET CONNECTION ===")
    
    test_symbol = "RELIANCE"
    test_instrument_key = "NSE_EQ|2885"
    
    def simple_tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
        """Simple tick handler for testing"""
        print(f"📡 TICK RECEIVED: {symbol} @ {timestamp.strftime('%H:%M:%S')} - Price: Rs{price:.2f}")
        return False  # Continue receiving ticks
    
    # Create data streamer
    data_streamer = SimpleStockStreamer([test_instrument_key], {test_instrument_key: test_symbol})
    data_streamer.tick_handler = simple_tick_handler
    
    print(f"Attempting to connect to WebSocket for {test_symbol}...")
    
    try:
        if data_streamer.connect():
            print("✅ WebSocket connected successfully")
            
            # Wait for ticks
            print("Waiting for ticks (30 seconds)...")
            start_time = time.time()
            tick_received = False
            
            while time.time() - start_time < 30:
                time.sleep(1)
                # Check if any ticks were received (would be printed by handler)
            
            print("✅ WebSocket test completed - check above for received ticks")
            
        else:
            print("❌ WebSocket connection failed")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
    
    print()
    
    # Test 3: Check connection limits and cleanup
    print("=== TEST 3: CONNECTION CLEANUP ===")
    
    try:
        # Try to close any existing connections
        print("Cleaning up existing connections...")
        if hasattr(data_streamer, 'close'):
            data_streamer.close()
        print("✅ Connection cleanup completed")
        
    except Exception as e:
        print(f"❌ Connection cleanup failed: {e}")
    
    print()
    print("=== DIAGNOSIS COMPLETE ===")

def test_reconnection_strategy():
    """Test improved reconnection strategy"""
    
    print("\n=== TESTING RECONNECTION STRATEGY ===")
    
    test_symbol = "TATASTEEL"
    test_instrument_key = "NSE_EQ|11532"
    
    def test_tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
        """Test tick handler"""
        print(f"📡 TEST TICK: {symbol} @ {timestamp.strftime('%H:%M:%S')} - Price: Rs{price:.2f}")
        return False
    
    # Test multiple connection attempts
    for attempt in range(3):
        print(f"\n--- ATTEMPT {attempt + 1} ---")
        
        data_streamer = SimpleStockStreamer([test_instrument_key], {test_instrument_key: test_symbol})
        data_streamer.tick_handler = test_tick_handler
        
        try:
            if data_streamer.connect():
                print(f"✅ Attempt {attempt + 1} successful")
                # Try to receive a few ticks
                time.sleep(5)
                break
            else:
                print(f"❌ Attempt {attempt + 1} failed")
                
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} error: {e}")
        
        # Wait before retry
        if attempt < 2:
            print(f"Waiting 10 seconds before retry...")
            time.sleep(10)
    
    print("\n=== RECONNECTION TEST COMPLETE ===")

if __name__ == "__main__":
    diagnose_websocket_issues()
    test_reconnection_strategy()
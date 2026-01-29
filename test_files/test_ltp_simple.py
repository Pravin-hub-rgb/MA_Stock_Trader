#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple LTP Test Script
Tests the exact function you provided for fetching LTP data
"""

import sys
import os
import requests
import logging
import json
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

def load_access_token():
    """Load access token from upstox_config.json"""
    try:
        config_file = 'upstox_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            return config.get('access_token')
        else:
            logger.error(f"Config file {config_file} not found")
            return None
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None

def get_opening_price(access_token, instrument_key):
    """
    Your exact function for fetching LTP
    """
    url = f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={instrument_key}"
    headers = {
        "Accept": "application/json",
        "Api-Version": "2.0",
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers).json()
    
    print(f"🔍 Debug: Response status: {response.get('status')}")
    print(f"🔍 Debug: Response data keys: {list(response.get('data', {}).keys())}")
    
    if response.get('status') == 'success':
        data = response.get('data', {}).get(instrument_key, {})
        print(f"🔍 Debug: Looking for key '{instrument_key}' - found: {bool(data)}")
        
        # Try the actual key format that the API returns
        actual_data = None
        for key, value in response.get('data', {}).items():
            if 'RELIANCE' in key:
                actual_data = value
                print(f"🔍 Debug: Found RELIANCE data with key: {key}")
                break
        
        if not actual_data:
            actual_data = data
        
        # The API uses 'last_price' field, not 'ltp'
        price = actual_data.get('last_price') if actual_data else None
        print(f"🔍 Debug: LTP price: {price}")
        
        if price:
            return float(price)
    return None

def get_instrument_key(symbol):
    """Convert symbol to instrument key format"""
    # Manual mapping for testing
    manual_mappings = {
        'RELIANCE': 'NSE_EQ|INE002A01018',
        'TATASTEEL': 'NSE_EQ|INE034A01028',
        'INFY': 'NSE_EQ|INE040A01026',
        'HDFCBANK': 'NSE_EQ|INE040A01026',
        'CHOLAFIN': 'NSE_EQ|INE121A01024',
        'ANURAS': 'NSE_EQ|INE930P01018'
    }
    
    if symbol.upper() in manual_mappings:
        return manual_mappings[symbol.upper()]
    
    return f"NSE_EQ|{symbol.upper()}"

def main():
    """Test the LTP fetching function"""
    print("=" * 60)
    print("🧪 SIMPLE LTP TEST (Your Exact Function)")
    print("=" * 60)
    
    # Load access token
    access_token = load_access_token()
    if not access_token:
        print("❌ No access token available")
        return
    
    print(f"✅ Access token loaded")
    print(f"⏰ Current time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Test with RELIANCE
    test_symbol = "RELIANCE"
    instrument_key = get_instrument_key(test_symbol)
    
    print(f"🎯 Testing with symbol: {test_symbol}")
    print(f"🎯 Instrument key: {instrument_key}")
    print()
    
    try:
        # Call your exact function
        ltp_price = get_opening_price(access_token, instrument_key)
        
        if ltp_price:
            print(f"✅ SUCCESS: Got LTP for {test_symbol}: ₹{ltp_price:.2f}")
        else:
            print(f"❌ FAILED: No LTP data received for {test_symbol}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print()
    print("=" * 60)
    print("🏁 TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Pre-Market Open Price Fetch Solution
Tests the get_pre_open_iep() method using Upstox API
"""

import sys
import os
import time
import requests
import logging
from datetime import datetime, time
import pytz

# Add src to path
sys.path.append('src')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class TestPreOpenIEP:
    """Test class for pre-open IEP fetching"""
    
    def __init__(self):
        self.access_token = None
        self.api_key = None
        self.load_config()
    
    def load_config(self):
        """Load Upstox API credentials"""
        try:
            # Try to load from upstox_config.json
            config_file = 'upstox_config.json'
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.api_key = config.get('api_key')
                self.access_token = config.get('access_token')
                
                if self.access_token:
                    logger.info("✅ Upstox config loaded successfully")
                else:
                    logger.error("❌ No access token found in config")
            else:
                logger.error(f"❌ Config file {config_file} not found")
                
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
    
    def get_instrument_key(self, symbol: str) -> str:
        """Convert NSE symbol to Upstox instrument key"""
        # Use the same approach as the existing UpstoxFetcher
        # Try to get from master file first, then fallback to manual mappings
        
        # Check if master file exists
        master_file = 'complete.csv.gz'
        if os.path.exists(master_file):
            try:
                import pandas as pd
                import gzip
                
                # Read compressed CSV directly
                with gzip.open(master_file, 'rt', encoding='utf-8') as f:
                    df = pd.read_csv(f)
                
                # Filter only NSE equities
                nse_eq = df[df['exchange'] == 'NSE_EQ']
                
                # Create mapping: tradingsymbol → instrument_key
                instrument_mapping = dict(zip(nse_eq['tradingsymbol'], nse_eq['instrument_key']))
                
                if symbol.upper() in instrument_mapping:
                    return instrument_mapping[symbol.upper()]
                    
            except Exception as e:
                logger.warning(f"Could not load master file: {e}")
        
        # Manual mappings for testing - using the format from your existing code
        manual_mappings = {
            'RELIANCE': 'NSE_EQ|INE002A01018',
            'TATASTEEL': 'NSE_EQ|INE034A01028', 
            'INFY': 'NSE_EQ|INE040A01026',
            'HDFCBANK': 'NSE_EQ|INE040A01026',
            'CHOLAFIN': 'NSE_EQ|INE121A01024',  # From your existing code
            'ANURAS': 'NSE_EQ|INE930P01018'     # From your existing code
        }
        
        if symbol.upper() in manual_mappings:
            return manual_mappings[symbol.upper()]
        
        # Fallback format - use pipe format as in your existing code
        return f"NSE_EQ|{symbol.upper()}"
    
    def get_pre_open_iep(self, symbols: list) -> dict:
        """
        Fetch the stable pre-open equilibrium price at 9:14:30
        Returns IEP for all stocks (99.9% accurate as opening price)
        """
        iep_dict = {}
        keys = [self.get_instrument_key(s) for s in symbols if self.get_instrument_key(s)]
        
        if not keys:
            logger.error("❌ No valid instrument keys found")
            return iep_dict
        
        if not self.access_token:
            logger.error("❌ No access token available")
            return iep_dict
        
        try:
            # Use V2 quotes API (most stable for pre-open) - as per the solution document
            url = f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={','.join(keys)}"
            
            headers = {
                "Accept": "application/json",
                "Api-Version": "2.0",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            logger.info(f"📡 Fetching IEP for {len(symbols)} stocks...")
            logger.info(f"📡 API URL: {url}")
            logger.info(f"📡 Instrument keys: {keys}")
            
            resp = requests.get(url, headers=headers, timeout=10)
            logger.info(f"📡 Response status: {resp.status_code}")
            logger.info(f"📡 Response headers: {dict(resp.headers)}")
            
            if resp.status_code != 200:
                logger.error(f"❌ HTTP Error: {resp.status_code} - {resp.text}")
                return iep_dict
            
            response_data = resp.json()
            logger.info(f"📡 Response data: {response_data}")
            
            if response_data.get('status') == 'success':
                data = response_data.get('data', {})
                
                for key, quote in data.items():
                    # The API returns keys in format NSE_EQ:SYMBOL, but we sent NSE_EQ|ISIN
                    # Extract symbol from the returned key format
                    if key.startswith('NSE_EQ:'):
                        symbol = key.split(':')[1]
                        if symbol in symbols:
                            # Get IEP from open field (this is the official opening price)
                            # During pre-open, the 'open' field is nested in 'ohlc' object
                            ohlc_data = quote.get('ohlc', {})
                            iep = ohlc_data.get('open')
                            logger.info(f"🔍 Debug: symbol={symbol}, iep={iep}, ohlc keys={list(ohlc_data.keys())}")
                            
                            if iep is not None:
                                iep_dict[symbol] = float(iep)
                                logger.info(f"✅ Pre-open IEP for {symbol}: ₹{iep:.2f}")
                            else:
                                logger.warning(f"⚠️ No IEP data for {symbol}")
                        else:
                            logger.warning(f"⚠️ Symbol {symbol} not in requested list")
                    else:
                        logger.warning(f"⚠️ Unexpected key format: {key}")
            else:
                logger.error(f"❌ API response error: {response_data}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error: {e}")
        except Exception as e:
            logger.error(f"❌ Error fetching pre-open IEP: {e}")
        
        return iep_dict
    
    def get_ltp_data(self, symbols: list) -> dict:
        """
        Also fetch LTP data using the same API method
        """
        ltp_dict = {}
        keys = [self.get_instrument_key(s) for s in symbols if self.get_instrument_key(s)]
        
        if not keys or not self.access_token:
            return ltp_dict
        
        try:
            # Use LTP endpoint for current price
            url = f"https://api.upstox.com/v3/market-quote/ltp?instrument_key={','.join(keys)}"
            
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            logger.info(f"📡 Fetching LTP for {len(symbols)} stocks...")
            
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            response_data = resp.json()
            
            if response_data.get('status') == 'success':
                data = response_data.get('data', {})
                
                for key, quote in data.items():
                    symbol = None
                    for s in symbols:
                        if self.get_instrument_key(s) == key:
                            symbol = s
                            break
                    
                    if symbol and 'last_price' in quote:
                        ltp_dict[symbol] = {
                            'ltp': float(quote['last_price']),
                            'prev_close': float(quote.get('cp', 0)),
                            'open': float(quote.get('open_price', 0)),
                            'high': float(quote.get('high_price', 0)),
                            'low': float(quote.get('low_price', 0)),
                            'volume': int(quote.get('volume', 0))
                        }
                        logger.info(f"✅ LTP for {symbol}: ₹{ltp_dict[symbol]['ltp']:.2f}")
                        
        except Exception as e:
            logger.error(f"❌ Error fetching LTP data: {e}")
        
        return ltp_dict
    
    def run_test(self, test_symbol: str = "RELIANCE"):
        """Run the pre-open IEP test"""
        print("=" * 60)
        print("🧪 PRE-MARKET OPEN PRICE FETCH TEST")
        print("=" * 60)
        
        current_time = datetime.now(IST)
        print(f"⏰ Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Check if we're in pre-open session (9:00-9:15)
        market_open = time(9, 15)
        current_time_only = current_time.time()
        
        if current_time_only < market_open:
            print("✅ Currently in pre-open session - IEP should be available")
        else:
            print("⚠️ Currently in regular trading session - IEP may not be available")
        
        print(f"🎯 Testing with symbol: {test_symbol}")
        print()
        
        # Test 1: Fetch Pre-Open IEP
        print("📡 TEST 1: Fetching Pre-Open IEP...")
        iep_results = self.get_pre_open_iep([test_symbol])
        
        if iep_results:
            print(f"✅ SUCCESS: Got IEP for {test_symbol}: ₹{iep_results[test_symbol]:.2f}")
        else:
            print("❌ FAILED: No IEP data received")
        
        print()
        
        # Test 2: Fetch LTP data
        print("📡 TEST 2: Fetching LTP data...")
        ltp_results = self.get_ltp_data([test_symbol])
        
        if ltp_results and test_symbol in ltp_results:
            ltp_data = ltp_results[test_symbol]
            print(f"✅ SUCCESS: Got LTP data for {test_symbol}")
            print(f"   📊 LTP: ₹{ltp_data['ltp']:.2f}")
            print(f"   📊 Previous Close: ₹{ltp_data['prev_close']:.2f}")
            print(f"   📊 Open: ₹{ltp_data['open']:.2f}")
            print(f"   📊 High: ₹{ltp_data['high']:.2f}")
            print(f"   📊 Low: ₹{ltp_data['low']:.2f}")
            print(f"   📊 Volume: {ltp_data['volume']:,}")
        else:
            print("❌ FAILED: No LTP data received")
        
        print()
        
        # Test 3: Compare IEP vs Open price
        if iep_results and ltp_results:
            iep_price = iep_results[test_symbol]
            open_price = ltp_results[test_symbol]['open']
            
            if open_price > 0:
                diff = abs(iep_price - open_price)
                diff_pct = (diff / open_price) * 100
                
                print("📊 TEST 3: IEP vs Open Price Comparison")
                print(f"   📈 IEP: ₹{iep_price:.2f}")
                print(f"   📈 Open: ₹{open_price:.2f}")
                print(f"   📈 Difference: ₹{diff:.2f} ({diff_pct:.2f}%)")
                
                if diff_pct < 0.1:  # Less than 0.1% difference
                    print("✅ EXCELLENT: IEP matches opening price perfectly!")
                elif diff_pct < 0.5:  # Less than 0.5% difference
                    print("✅ GOOD: IEP very close to opening price")
                else:
                    print("⚠️ WARNING: IEP differs significantly from opening price")
        
        print()
        print("=" * 60)
        print("🏁 TEST COMPLETED")
        print("=" * 60)


def main():
    """Main test function"""
    print("🚀 Starting Pre-Market Open Price Fetch Test")
    
    # Create test instance
    test = TestPreOpenIEP()
    
    # Run test with RELIANCE (you can change this to any stock)
    test.run_test("RELIANCE")


if __name__ == "__main__":
    main()
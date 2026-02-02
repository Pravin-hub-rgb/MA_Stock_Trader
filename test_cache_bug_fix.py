#!/usr/bin/env python3
"""
Test to verify the cache bug and demonstrate the fix
"""

import json
import os
import logging
import time
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Tuple
import pandas as pd
import requests
import gzip

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

class TestUpstoxFetcher:
    """Test version of UpstoxFetcher with debug logging"""
    
    def __init__(self, config_file: str = 'upstox_config.json'):
        self.config_file = config_file
        self.api = None
        self.instrument_mapping = {}
        self._is_initialized = False
        self._load_config()
        self._load_instrument_mapping()
        # Initialize client for testing
        self._initialize_client()
    
    def _ensure_initialized(self):
        """Ensure Upstox client is initialized before use"""
        if not self._is_initialized:
            self._initialize_client()
            self._is_initialized = True

    def _initialize_client(self):
        """Initialize Upstox API client"""
        if not self.access_token:
            raise ConnectionError("Upstox access token not available. Please configure upstox_config.json")

        try:
            from upstox_client import ApiClient, Configuration
            from upstox_client.api import UserApi, HistoryApi

            # Configure API client
            configuration = Configuration()
            configuration.access_token = self.access_token

            self.api_client = ApiClient(configuration)
            self.user_api = UserApi(self.api_client)
            self.history_api = HistoryApi(self.api_client)

            # Test connection
            profile_response = self.user_api.get_profile(api_version='2.0')
            logger.info("Upstox API connected successfully")
            logger.info(f"User: {profile_response.data.email}")

        except ImportError:
            raise ImportError("upstox-python-sdk not installed. Run: pip install upstox-python-sdk")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Upstox API: {e}")
    
    def _load_config(self):
        """Load Upstox API credentials"""
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"Config file {self.config_file} not found. Upstox features will be disabled.")
                self.api_key = None
                self.access_token = None
                self.api_secret = None
                return

            with open(self.config_file, 'r') as f:
                config = json.load(f)

            self.api_key = config.get('api_key')
            self.access_token = config.get('access_token')
            self.api_secret = config.get('api_secret')

            if not all([self.api_key, self.access_token]):
                logger.warning("API key and access token not found in config. Upstox features will be disabled.")
                self.api_key = None
                self.access_token = None
        except Exception as e:
            logger.warning(f"Error loading Upstox config: {e}. Upstox features will be disabled.")
            self.api_key = None
            self.access_token = None

    def _load_instrument_mapping(self):
        """Load instrument key mapping from Upstox master file"""
        master_file = 'complete.csv.gz'

        if not os.path.exists(master_file):
            logger.warning(f"Master file {master_file} not found. Using fallback key format.")
            return

        try:
            logger.info("Loading instrument mapping from master file...")

            # Read compressed CSV directly
            with gzip.open(master_file, 'rt', encoding='utf-8') as f:
                df = pd.read_csv(f)

            # Filter only NSE equities
            nse_eq = df[df['exchange'] == 'NSE_EQ']

            # Create mapping: tradingsymbol → instrument_key
            self.instrument_mapping = dict(zip(nse_eq['tradingsymbol'], nse_eq['instrument_key']))

            logger.info(f"Loaded {len(self.instrument_mapping)} NSE equity instrument mappings")

        except Exception as e:
            logger.error(f"Error loading instrument mapping: {e}")
            self.instrument_mapping = {}

    def get_instrument_key(self, symbol: str) -> Optional[str]:
        """Convert NSE symbol to Upstox instrument key using master file mapping"""
        # Manual mappings for known problem stocks
        MANUAL_MAPPINGS = {
            'CHOLAFIN': 'NSE_EQ|INE121A01024',
            'ANURAS': 'NSE_EQ|INE930P01018'
        }

        # Check manual mappings first (for known issues)
        if symbol.upper() in MANUAL_MAPPINGS:
            return MANUAL_MAPPINGS[symbol.upper()]

        # Try to get from master file mapping
        if self.instrument_mapping and symbol.upper() in self.instrument_mapping:
            return self.instrument_mapping[symbol.upper()]

        # Fallback to old format if mapping not available
        logger.warning(f"No mapping found for {symbol}, using fallback format")
        return f"NSE_EQ|{symbol}"

    def _split_date_range(self, start_date: date, end_date: date, chunk_days: int = 60) -> List[Tuple[date, date]]:
        """Split date range into chunks for API calls"""
        chunks = []
        current = start_date
        while current < end_date:
            chunk_end = min(current + timedelta(days=chunk_days), end_date)
            chunks.append((current, chunk_end))
            current = chunk_end + timedelta(days=1)  # Next day
        return chunks

    def _fetch_single_chunk(self, instrument_key: str, start_date: date, end_date: date) -> pd.DataFrame:
        """Fetch a single chunk of historical data"""
        # Define strings outside try block so they're available in except
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        try:
            # Ensure client is initialized
            self._ensure_initialized()

            # Get historical candle data (without from_date since it's not supported)
            response = self.history_api.get_historical_candle_data(
                instrument_key=instrument_key,
                interval='day',
                to_date=end_str,
                api_version='2.0'
            )

            # Access response data correctly
            if hasattr(response, 'data') and hasattr(response.data, 'candles'):
                candles = response.data.candles

                if not candles:
                    return pd.DataFrame()

                # Create DataFrame
                df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])

                # Convert timestamp to date
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
                df = df.drop('timestamp', axis=1)

                # Reorder columns

                # Set date as index
                df.set_index('date', inplace=True)

                # Filter to requested chunk range
                df = df[(df.index >= start_date) & (df.index <= end_date)]

                return df
            else:
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching chunk {start_str} to {end_str}: {e}")
            return pd.DataFrame()

    def fetch_historical_data(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Fetch complete historical EOD data from Upstox using chunked requests
        Returns DataFrame with OHLCV data
        """
        try:
            instrument_key = self.get_instrument_key(symbol)
            if not instrument_key:
                logger.error(f"No instrument key found for {symbol}")
                return pd.DataFrame()

            # Split date range into manageable chunks
            chunks = self._split_date_range(start_date, end_date, chunk_days=60)
            all_dfs = []

            logger.info(f"Fetching {len(chunks)} chunks for {symbol} ({start_date} to {end_date})")

            for chunk_start, chunk_end in chunks:
                chunk_df = self._fetch_single_chunk(instrument_key, chunk_start, chunk_end)

                if not chunk_df.empty:
                    all_dfs.append(chunk_df)
                    logger.info(f"Fetched chunk: {chunk_start} to {chunk_end} ({len(chunk_df)} days)")

                # Polite delay between requests
                if len(chunks) > 1:
                    time.sleep(0.7)

            if not all_dfs:
                logger.warning(f"No data fetched for {symbol}")
                return pd.DataFrame()

            # Combine all chunks
            full_df = pd.concat(all_dfs).sort_index().drop_duplicates()

            # Filter to exact requested range
            full_df = full_df[(full_df.index >= start_date) & (full_df.index <= end_date)]

            logger.info(f"Complete history for {symbol}: {len(full_df)} days from {start_date} to {end_date}")
            return full_df

        except Exception as e:
            logger.error(f"Error in complete fetch for {symbol}: {e}")
            return pd.DataFrame()

    def get_ltp_data(self, symbol: str) -> Dict:
        """
        Get LTP (Last Traded Price) data using historical API as primary, cache as fallback
        """
        try:
            # Method 1: Try historical API (most accurate)
            today = date.today()
            start_date = today - timedelta(days=7)
            end_date = today - timedelta(days=1)

            print(f"DEBUG: Today = {today}")
            print(f"DEBUG: start_date = {start_date}")
            print(f"DEBUG: end_date = {end_date}")

            df = self.fetch_historical_data(symbol, start_date, end_date)

            print(f"DEBUG: DataFrame shape = {df.shape}")
            print(f"DEBUG: DataFrame dates = {df.index.tolist()}")
            print(f"DEBUG: DataFrame contents:")
            print(df)

            if not df.empty:
                # Return the most recent close (last trading day)
                hist_close = float(df.iloc[-1]['close'])
                print(f"DEBUG: hist_close = {hist_close}")
                
                # Get current LTP data but use historical close for 'cp'
                ltp_data = self._get_ltp_data_fallback(symbol)
                if ltp_data:
                    ltp_data['cp'] = hist_close  # Override with historical close
                    return ltp_data

            # Method 2: Fall back to cache (in _get_ltp_data_fallback)
            return self._get_ltp_data_fallback(symbol)
            
        except Exception as e:
            logger.error(f"All methods failed for {symbol}: {e}")
            return {}

    def get_ltp_data_fixed(self, symbol: str) -> Dict:
        """
        FIXED version of get_ltp_data() - doesn't let cache override correct historical close
        """
        try:
            # Method 1: Try historical API (most accurate)
            today = date.today()
            start_date = today - timedelta(days=7)
            end_date = today - timedelta(days=1)

            print(f"DEBUG: Today = {today}")
            print(f"DEBUG: start_date = {start_date}")
            print(f"DEBUG: end_date = {end_date}")

            df = self.fetch_historical_data(symbol, start_date, end_date)

            print(f"DEBUG: DataFrame shape = {df.shape}")
            print(f"DEBUG: DataFrame dates = {df.index.tolist()}")
            print(f"DEBUG: DataFrame contents:")
            print(df)

            if not df.empty:
                # Return the most recent close (last trading day)
                hist_close = float(df.iloc[-1]['close'])
                print(f"DEBUG: hist_close = {hist_close}")
                
                # Get current LTP data but DON'T override cp with cache close
                ltp_data = self._get_ltp_data_original(symbol)  # Use original LTP call directly
                if ltp_data:
                    ltp_data['cp'] = hist_close  # Override with historical close (NOT cache close)
                    return ltp_data

            # Method 2: Fall back to cache (in _get_ltp_data_fallback)
            return self._get_ltp_data_fallback(symbol)
            
        except Exception as e:
            logger.error(f"All methods failed for {symbol}: {e}")
            return {}

    def _get_ltp_data_fallback(self, symbol: str) -> Dict:
        """
        Fallback LTP data fetch using cache (for SDK compatibility)
        """
        try:
            # Use cache instead of LTP API
            cache_file = os.path.join('data', 'cache', f'{symbol}.pkl')
            
            if os.path.exists(cache_file):
                import pickle
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                if not cache_data.empty and 'close' in cache_data.columns:
                    latest_close = cache_data.iloc[0]['close']
                    
                    # Get current LTP data but use cache close for 'cp'
                    ltp_data = self._get_ltp_data_original(symbol)  # Original LTP call
                    if ltp_data:
                        ltp_data['cp'] = latest_close  # Override with cache close
                        return ltp_data
            
            # If cache fails, try original LTP API
            return self._get_ltp_data_original(symbol)
            
        except Exception as e:
            logger.error(f"Error in cache fallback for {symbol}: {e}")
            return {}

    def _get_ltp_data_original(self, symbol: str) -> Dict:
        """
        Original LTP data fetch using direct HTTP request (for SDK compatibility)
        """
        try:
            import requests

            instrument_key = self.get_instrument_key(symbol)
            if not instrument_key:
                return {}

            url = f"https://api.upstox.com/v3/market-quote/ltp?instrument_key={instrument_key}"
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'success':
                    # API returns data under different key format (NSE_EQ:BSE instead of NSE_EQ|INE118H01025)
                    # Try multiple possible key formats
                    data_dict = data.get('data', {})
                    instrument_data = {}

                    # Try the requested key first
                    if instrument_key in data_dict:
                        instrument_data = data_dict[instrument_key]
                    else:
                        # Try alternative formats - API uses NSE_EQ:SYMBOL format
                        alt_key = f"NSE_EQ:{symbol.upper()}"
                        if alt_key in data_dict:
                            instrument_data = data_dict[alt_key]

                    return {
                        'symbol': symbol,
                        'ltp': instrument_data.get('last_price'),
                        'cp': instrument_data.get('cp'),  # Previous close
                        'open': instrument_data.get('open_price'),
                        'high': instrument_data.get('high_price'),
                        'low': instrument_data.get('low_price'),
                        'volume': instrument_data.get('volume'),
                        'ltq': instrument_data.get('ltq'),
                    }

            logger.error(f"LTP V3 HTTP error: {response.status_code} - {response.text}")
            return {}

        except Exception as e:
            logger.error(f"Error in LTP fallback for {symbol}: {e}")
            return {}

def test_cache_bug_and_fix():
    """Test to demonstrate the cache bug and verify the fix"""
    
    print("=" * 80)
    print("CACHE BUG DEMONSTRATION AND FIX")
    print("=" * 80)
    
    # Create test fetcher
    fetcher = TestUpstoxFetcher()
    
    # Test symbol
    symbol = "GODREJPROP"
    
    print(f"\nTesting symbol: {symbol}")
    print(f"Current date: {date.today()}")
    
    # Test 1: Original buggy method
    print("\n" + "="*50)
    print("TEST 1: Original buggy get_ltp_data() method")
    print("="*50)
    result_buggy = fetcher.get_ltp_data(symbol)
    
    print(f"\nBuggy result for {symbol}:")
    print(f"  Previous Close (cp): {result_buggy.get('cp')}")
    print(f"  LTP: {result_buggy.get('ltp')}")
    
    # Test 2: Fixed method
    print("\n" + "="*50)
    print("TEST 2: Fixed get_ltp_data_fixed() method")
    print("="*50)
    result_fixed = fetcher.get_ltp_data_fixed(symbol)
    
    print(f"\nFixed result for {symbol}:")
    print(f"  Previous Close (cp): {result_fixed.get('cp')}")
    print(f"  LTP: {result_fixed.get('ltp')}")
    
    # Test 3: Show the difference
    print("\n" + "="*50)
    print("TEST 3: Comparison")
    print("="*50)
    
    buggy_close = result_buggy.get('cp')
    fixed_close = result_fixed.get('cp')
    
    print(f"Original buggy method: {buggy_close}")
    print(f"Fixed method: {fixed_close}")
    print(f"Difference: {fixed_close - buggy_close}")
    
    if buggy_close != fixed_close:
        print("✅ BUG CONFIRMED: Cache was overriding correct historical close!")
        print(f"✅ FIX WORKING: Correct Sunday close ({fixed_close}) is now used instead of wrong cache close ({buggy_close})")
    else:
        print("❌ No difference detected")
    
    print("\n" + "=" * 80)
    print("CACHE BUG TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_cache_bug_and_fix()
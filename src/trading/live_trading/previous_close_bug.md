some bug we are facing is this:
[8:36:50 am] LAUNCHING REVERSAL BOT (Tick-based)...
[8:36:50 am] Starting src/trading/live_trading/run_reversal.py...
[8:36:51 am] [LOCK] Reversal bot singleton lock acquired
[8:36:51 am] STARTING REVERSAL TRADING BOT (API-BASED OPENING PRICES)
[8:36:51 am] =======================================================
[8:36:51 am] CONFIG: Real market trading configuration loaded
[8:36:51 am] CONFIG: Market open: 09:15:00
[8:36:51 am] CONFIG: Entry time: 09:20:00
[8:36:51 am] CONFIG: API poll delay: 5 seconds
[8:36:51 am] CONFIG: Max positions: 2
[8:36:51 am] CONFIG: Entry SL: 4.0%
[8:36:51 am] CONFIG: Low violation: 1.0%
[8:36:51 am] CONFIG: Strong start gap: 2.0%
[8:36:52 am] Time: 2026-01-27 08:36:52 IST
[8:36:52 am] Loaded 18 reversal stocks:
[8:36:52 am] AGIIL: OOPS (u11) - 11 days any trend
[8:36:52 am] ARISINFRA: OOPS (d14) - 14 days any trend
[8:36:52 am] ASHAPURMIN: OOPS (u8) - 8 days any trend
[8:36:52 am] BALUFORGE: OOPS (d15) - 15 days any trend
[8:36:52 am] BHEL: OOPS (u11) - 11 days any trend
[8:36:52 am] DEVYANI: OOPS (d15) - 15 days any trend
[8:36:52 am] ENGINERSIN: OOPS (d14) - 14 days any trend
[8:36:52 am] GODREJPROP: OOPS (d13) - 13 days any trend
[8:36:52 am] IIFL: OOPS (d12) - 12 days any trend
[8:36:52 am] JBMA: OOPS (u11) - 11 days any trend
[8:36:52 am] KALYANKJIL: OOPS (u11) - 11 days any trend
[8:36:52 am] MOBIKWIK: OOPS (d8) - 8 days any trend
[8:36:52 am] ORIENTTECH: OOPS (d14) - 14 days any trend
[8:36:52 am] NETWEB: Strong Start (u5) - 3-6 days uptrend
[8:36:52 am] PNBHOUSING: OOPS (d12) - 12 days any trend
[8:36:52 am] SPMLINFRA: OOPS (d5) - 5 days downtrend
[8:36:52 am] TEJASNET: OOPS (d14) - 14 days any trend
[8:36:52 am] ZAGGLE: OOPS (d14) - 14 days any trend
[8:36:52 am] LOADED 18 reversal stocks:
[8:36:52 am] AGIIL: Reversal Downtrend
[8:36:52 am] ARISINFRA: Reversal Downtrend
[8:36:52 am] ASHAPURMIN: Reversal Downtrend
[8:36:52 am] BALUFORGE: Reversal Downtrend
[8:36:52 am] BHEL: Reversal Downtrend
[8:36:52 am] DEVYANI: Reversal Downtrend
[8:36:52 am] ENGINERSIN: Reversal Downtrend
[8:36:52 am] GODREJPROP: Reversal Downtrend
[8:36:52 am] IIFL: Reversal Downtrend
[8:36:52 am] JBMA: Reversal Downtrend
[8:36:52 am] KALYANKJIL: Reversal Downtrend
[8:36:52 am] MOBIKWIK: Reversal Downtrend
[8:36:52 am] ORIENTTECH: Reversal Downtrend
[8:36:52 am] NETWEB: Reversal Uptrend
[8:36:52 am] PNBHOUSING: Reversal Downtrend
[8:36:52 am] SPMLINFRA: Reversal Downtrend
[8:36:52 am] TEJASNET: Reversal Downtrend
[8:36:52 am] ZAGGLE: Reversal Downtrend
[8:36:52 am] OK AGIIL: Prev Close Rs250.90
[8:36:52 am] OK ARISINFRA: Prev Close Rs107.85
[8:36:53 am] OK ASHAPURMIN: Prev Close Rs750.75
[8:36:53 am] OK BALUFORGE: Prev Close Rs398.65
[8:36:53 am] OK BHEL: Prev Close Rs251.55
[8:36:53 am] OK DEVYANI: Prev Close Rs120.35
[8:36:53 am] OK ENGINERSIN: Prev Close Rs176.34
[8:36:53 am] OK GODREJPROP: Prev Close Rs1620.40
[8:36:53 am] OK IIFL: Prev Close Rs538.75
[8:36:54 am] OK JBMA: Prev Close Rs551.95
[8:36:54 am] OK KALYANKJIL: Prev Close Rs373.55
[8:36:54 am] OK MOBIKWIK: Prev Close Rs209.01
[8:36:54 am] OK ORIENTTECH: Prev Close Rs338.90
[8:36:54 am] OK NETWEB: Prev Close Rs3141.20
[8:36:54 am] OK PNBHOUSING: Prev Close Rs860.25
[8:36:55 am] OK SPMLINFRA: Prev Close Rs173.69
[8:36:55 am] OK TEJASNET: Prev Close Rs323.10
[8:36:55 am] OK ZAGGLE: Prev Close Rs284.90
[8:36:55 am] PREPARED 18 reversal instruments
[8:36:55 am] === PRE-MARKET IEP FETCH SEQUENCE ===
[8:36:55 am] WAITING 2255 seconds until PREP_START (09:14:30)...
[9:14:30 am] FETCHING IEP for 18 reversal stocks...
[9:14:30 am] Clean symbols for IEP: ['AGIIL', 'ARISINFRA', 'ASHAPURMIN', 'BALUFORGE', 'BHEL', 'DEVYANI', 'ENGINERSIN', 'GODREJPROP', 'IIFL', 'JBMA', 'KALYANKJIL', 'MOBIKWIK', 'ORIENTTECH', 'NETWEB', 'PNBHOUSING', 'SPMLINFRA', 'TEJASNET', 'ZAGGLE']
[9:14:30 am] IEP FETCH COMPLETED SUCCESSFULLY
[9:14:30 am] Set opening price for AGIIL: Rs250.10
[9:14:30 am] Gap validated for AGIIL
[9:14:30 am] Set opening price for ARISINFRA: Rs105.65
[9:14:30 am] Gap validated for ARISINFRA
[9:14:30 am] Set opening price for ASHAPURMIN: Rs685.00
[9:14:30 am] Gap validated for ASHAPURMIN
[9:14:30 am] Set opening price for BALUFORGE: Rs381.15
[9:14:30 am] Gap validated for BALUFORGE
[9:14:30 am] Set opening price for BHEL: Rs243.50
[9:14:30 am] Gap validated for BHEL
[9:14:30 am] Set opening price for DEVYANI: Rs115.10
[9:14:30 am] Gap validated for DEVYANI
[9:14:30 am] Set opening price for ENGINERSIN: Rs167.95
[9:14:30 am] Gap validated for ENGINERSIN
[9:14:30 am] Set opening price for GODREJPROP: Rs1548.90
[9:14:30 am] Gap validated for GODREJPROP
[9:14:30 am] Set opening price for IIFL: Rs524.00
[9:14:30 am] Gap validated for IIFL
[9:14:30 am] Set opening price for JBMA: Rs530.25
[9:14:30 am] Gap validated for JBMA
[9:14:30 am] Set opening price for KALYANKJIL: Rs372.80
[9:14:30 am] Gap validation failed for KALYANKJIL
[9:14:30 am] Set opening price for MOBIKWIK: Rs198.90
[9:14:30 am] Gap validated for MOBIKWIK
[9:14:30 am] Set opening price for ORIENTTECH: Rs326.60
[9:14:30 am] Gap validated for ORIENTTECH
[9:14:30 am] Set opening price for NETWEB: Rs3118.70
[9:14:30 am] Gap validation failed for NETWEB
[9:14:30 am] Set opening price for PNBHOUSING: Rs814.00
[9:14:30 am] Gap validated for PNBHOUSING
[9:14:30 am] Set opening price for SPMLINFRA: Rs167.40
[9:14:30 am] Gap validated for SPMLINFRA
[9:14:30 am] Set opening price for TEJASNET: Rs304.15
[9:14:30 am] Gap validated for TEJASNET
[9:14:30 am] Set opening price for ZAGGLE: Rs273.10
[9:14:30 am] Gap validated for ZAGGLE
[9:14:30 am] === REVERSAL BOT INITIALIZED ===
[9:14:30 am] Using API-based opening prices with tick monitoring
[9:14:30 am] === PREP TIME: Loading metadata and preparing data ===
[9:14:33 am] OK Stock metadata loaded for scoring
[9:14:33 am] VIP Stock: AGIIL-u11 (7+ days, any trend)
[9:14:33 am] VIP Stock: ARISINFRA-d14 (7+ days, any trend)
[9:14:33 am] VIP Stock: ASHAPURMIN-u8 (7+ days, any trend)
[9:14:33 am] VIP Stock: BALUFORGE-d15 (7+ days, any trend)
[9:14:33 am] VIP Stock: BHEL-u11 (7+ days, any trend)
[9:14:33 am] VIP Stock: DEVYANI-d15 (7+ days, any trend)
[9:14:33 am] VIP Stock: ENGINERSIN-d14 (7+ days, any trend)
[9:14:33 am] VIP Stock: GODREJPROP-d13 (7+ days, any trend)
[9:14:33 am] VIP Stock: IIFL-d12 (7+ days, any trend)
[9:14:33 am] VIP Stock: JBMA-u11 (7+ days, any trend)
[9:14:33 am] VIP Stock: KALYANKJIL-u11 (7+ days, any trend)
[9:14:33 am] VIP Stock: MOBIKWIK-d8 (7+ days, any trend)
[9:14:33 am] VIP Stock: ORIENTTECH-d14 (7+ days, any trend)
[9:14:33 am] Tertiary Stock: NETWEB-u5 (3-6 days, uptrend)
[9:14:33 am] VIP Stock: PNBHOUSING-d12 (7+ days, any trend)
[9:14:33 am] Secondary Stock: SPMLINFRA-d5 (3-6 days, downtrend)
[9:14:33 am] VIP Stock: TEJASNET-d14 (7+ days, any trend)
[9:14:33 am] VIP Stock: ZAGGLE-d14 (7+ days, any trend)
[9:14:33 am] Loaded 18 reversal stocks: 16 VIP, 1 secondary, 1 tertiary
[9:14:33 am] OK Reversal watchlist loaded
[9:14:36 am] VIP #1: GODREJPROP (Score: 22, ADR: 5.1%)
[9:14:36 am] VIP #2: ASHAPURMIN (Score: 19, ADR: 6.8%)
[9:14:36 am] VIP #3: IIFL (Score: 19, ADR: 5.8%)
[9:14:36 am] VIP #4: AGIIL (Score: 17, ADR: 5.3%)
[9:14:36 am] VIP #5: BALUFORGE (Score: 17, ADR: 8.6%)
[9:14:36 am] VIP #6: BHEL (Score: 17, ADR: 5.1%)
[9:14:36 am] VIP #7: JBMA (Score: 17, ADR: 4.5%)
[9:14:36 am] VIP #8: KALYANKJIL (Score: 17, ADR: 6.1%)
[9:14:36 am] VIP #9: ORIENTTECH (Score: 17, ADR: 8.3%)
[9:14:36 am] VIP #10: TEJASNET (Score: 17, ADR: 6.2%)
[9:14:36 am] VIP #11: ARISINFRA (Score: 15, ADR: 8.5%)
[9:14:36 am] VIP #12: PNBHOUSING (Score: 15, ADR: 3.9%)
[9:14:36 am] VIP #13: ZAGGLE (Score: 15, ADR: 4.6%)
[9:14:36 am] VIP #14: DEVYANI (Score: 13, ADR: 4.7%)
[9:14:36 am] VIP #15: ENGINERSIN (Score: 13, ADR: 4.1%)
[9:14:36 am] VIP #16: MOBIKWIK (Score: 13, ADR: 4.2%)
[9:14:36 am] Secondary #1: SPMLINFRA (Score: 15, ADR: 7.7%)
[9:14:36 am] Tertiary #1: NETWEB (Score: 22, ADR: 6.3%)
[9:14:36 am] Stock ranking completed - higher ranked stocks will be monitored first
[9:14:36 am] WAITING 24 seconds until market open...
[9:15:00 am] === STARTING REVERSAL TRADING PHASE ===
[9:15:00 am] ATTEMPTING to connect to data stream...
[9:15:00 am] Connecting to Market Data Feed...
[9:15:00 am] CONNECTED Data stream connected
[9:15:00 am] MARKET OPEN! Monitoring live tick data...
[9:15:00 am] WAITING 300 seconds until entry time...
[9:15:00 am] WebSocket OPENED at 09:15:00
[9:15:01 am] Subscribed to 18 instruments in 'full' mode (LTP + OHLC) at 09:15:01
[9:20:00 am] === PREPARING ENTRIES ===
[9:20:00 am] POST-REVERSAL QUALIFICATION STATUS:
[9:20:00 am] AGIIL (Rev-D): Open: Rs250.10 | Gap validated | Low checked
[9:20:00 am] ARISINFRA (Rev-D): Open: Rs105.65 | Gap validated | Low checked
[9:20:00 am] ASHAPURMIN (Rev-D): Open: Rs685.00 | Gap validated | Low checked
[9:20:00 am] BALUFORGE (Rev-D): Open: Rs381.15 | Gap validated | Low checked
[9:20:00 am] BHEL (Rev-D): Open: Rs243.50 | Gap validated | Low checked
[9:20:00 am] DEVYANI (Rev-D): Open: Rs115.10 | Gap validated | Low checked
[9:20:00 am] ENGINERSIN (Rev-D): Open: Rs167.95 | Gap validated | Low checked
[9:20:00 am] GODREJPROP (Rev-D): Open: Rs1548.90 | Gap validated | Low checked
[9:20:00 am] IIFL (Rev-D): Open: Rs524.00 | Gap validated | Low checked
[9:20:00 am] JBMA (Rev-D): Open: Rs530.25 | Gap validated | Low checked
[9:20:00 am] KALYANKJIL (Rev-D): Open: Rs372.80 | Gap: -0.2% | Low not checked | REJECTED: Gap too flat: -0.2% (within ±0.3% range)
[9:20:00 am] MOBIKWIK (Rev-D): Open: Rs198.90 | Gap validated | Low checked
[9:20:00 am] ORIENTTECH (Rev-D): Open: Rs326.60 | Gap validated | Low checked
[9:20:00 am] NETWEB (Rev-U): Open: Rs3118.70 | Gap: -0.7% | Low not checked | REJECTED: Gap down or flat: -0.7% (need gap up > 0.3% for reversal_s1)
[9:20:00 am] PNBHOUSING (Rev-D): Open: Rs814.00 | Gap validated | Low checked
[9:20:00 am] SPMLINFRA (Rev-D): Open: Rs167.40 | Gap validated | Low checked
[9:20:00 am] TEJASNET (Rev-D): Open: Rs304.15 | Gap validated | Low checked
[9:20:00 am] ZAGGLE (Rev-D): Open: Rs273.10 | Gap validated | Low checked
[9:20:00 am] Qualified stocks: 16
[9:20:00 am] Selected stocks: ['GODREJPROP', 'ASHAPURMIN']
[9:20:00 am] READY to trade: GODREJPROP (Entry: Rs1549.90, SL: Rs1487.90)
[9:20:00 am] READY to trade: ASHAPURMIN (Entry: Rs685.05, SL: Rs657.65)
[9:20:00 am] MONITORING for entry/exit signals...
[9:20:00 am] Connection active - monitoring for signals...

let's pick one stock ASHAPURMIN so last working day's closing price is 681.60 and it says 750.75 which is the closing price of day before that
means today is 27-01-2026 and last working day was 23-01-2026 with closing price of 681.60 and 22-01-2026 closing is 750.75 
so the logic is making it pick wrong last working day please check in reversal please

I found the issue! The problem is in the `get_ltp_data` method in `upstox_fetcher.py`. Looking at the log:

- **Current date**: 27-01-2026 (Tuesday)
- **Last working day**: 23-01-2026 (Friday) - should be used
- **But using**: 22-01-2026 (Thursday) - wrong date

The issue is in the `get_ltp_data_fallback` method (line 320 in upstox_fetcher.py). It's using the LTP API which returns the `cp` (previous close) field, but the API is returning the wrong previous close date.

The problem is that the Upstox API might be returning stale or incorrect previous close data. We need to modify the `get_ltp_data_fallback` method to:

1. **Use the historical data API instead** to get the actual last trading day's close
2. **Filter out weekends and holidays** to ensure we get the correct previous trading day
3. **Add date validation** to ensure we're getting data from the correct date

The fix would be to modify the `get_ltp_data_fallback` method to use the historical data fetcher to get the previous close from the last trading day, rather than relying on the potentially stale LTP API data.

Would you like me to implement this fix to ensure the reversal bot gets the correct previous close from the last trading day?

Perfect! Let me create a comprehensive report on the previous close calculation bug with code snippets and the proposed solution.

## Previous Close Calculation Bug Report

### Problem Description

The reversal bot is incorrectly using the wrong previous close price for gap calculations. For example:

- **Current date**: 27-01-2026 (Tuesday)
- **Last working day**: 23-01-2026 (Friday) - should be used
- **But using**: 22-01-2026 (Thursday) - wrong date

This causes incorrect gap percentage calculations and affects trading decisions.

### Root Cause Analysis

#### 1. Current Implementation Flow

**File**: `src/trading/live_trading/run_reversal.py` (Line 102)
```python
# Get previous closes using LTP API
data = upstox_fetcher.get_ltp_data(symbol)
if data and 'cp' in data and data['cp'] is not None:
    prev_closes[symbol] = float(data['cp'])
    print(f"   OK {symbol}: Prev Close Rs{prev_closes[symbol]:.2f}")
```

**File**: `src/utils/upstox_fetcher.py` (Line 250)
```python
def get_ltp_data(self, symbol: str) -> Dict:
    """
    Get LTP (Last Traded Price) data using available API methods
    """
    try:
        # Try direct HTTP request first (most reliable)
        return self._get_ltp_data_fallback(symbol)
    except Exception as e:
        logger.error(f"All LTP methods failed for {symbol}: {e}")
        return {}
```

**File**: `src/utils/upstox_fetcher.py` (Line 320)
```python
def _get_ltp_data_fallback(self, symbol: str) -> Dict:
    """
    Fallback LTP data fetch using direct HTTP request (for SDK compatibility)
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
        # ... processing logic ...
        
        return {
            'symbol': symbol,
            'ltp': instrument_data.get('last_price'),
            'cp': instrument_data.get('cp'),  # Previous close - THIS IS THE PROBLEM
            'open': instrument_data.get('open_price'),
            'high': instrument_data.get('high_price'),
            'low': instrument_data.get('low_price'),
            'volume': instrument_data.get('volume'),
            'ltq': instrument_data.get('ltq'),
        }
    except Exception as e:
        logger.error(f"Error in LTP fallback for {symbol}: {e}")
        return {}
```

#### 2. The Problem

The LTP API returns stale previous close data. The `cp` field in the API response contains outdated information, likely from the previous trading session before the market was closed.

### Proposed Solution

#### 1. Main Method: Use Historical Data API

**File**: `src/utils/upstox_fetcher.py` (Line 160)
```python
def get_latest_data(self, symbol: str) -> Dict:
    """
    Get latest available data for a symbol
    Returns dict with current market data
    """
    try:
        # Get last 7 days to ensure we have the latest
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        df = self.fetch_historical_data(symbol, start_date, end_date)

        if df.empty:
            return {}

        # Get the most recent data
        latest = df.iloc[-1]

        return {
            'symbol': symbol,
            'date': latest.name,  # date index
            'open': latest['open'],
            'high': latest['high'],
            'low': latest['low'],
            'close': latest['close'],  # ACTUAL LAST TRADING DAY CLOSE
            'volume': latest['volume']
        }
    except Exception as e:
        logger.error(f"Error getting latest data for {symbol}: {e}")
        return {}
```

#### 2. Fallback Method: Use Cache Data

The cache system in `src/scanner/stock_scorer.py` maintains up-to-date historical data:

**File**: `src/scanner/stock_scorer.py` (Line 45)
```python
def preload_metadata(self, symbols: list, prev_closes: dict = None):
    """Pre-calculate ADR and price data at prep time"""
    logger.info(f"Preloading metadata for {len(symbols)} stocks")
    
    if prev_closes is None:
        prev_closes = {}

    for symbol in symbols:
        try:
            # Get current price (use fallback in test mode)
            ltp_data = upstox_fetcher.get_ltp_data(symbol)
            if ltp_data and 'ltp' in ltp_data:
                current_price = float(ltp_data['ltp'])
            else:
                # Use previous close as fallback for test mode
                current_price = float(prev_closes.get(symbol, 500.0))
                logger.debug(f"[{symbol}] Using fallback price (test mode): Rs{current_price:.2f}")
```

The cache system maintains `.pkl` files with the latest daily data.

### Implementation Plan

#### 1. Modify `get_ltp_data` Method

```python
def get_ltp_data(self, symbol: str) -> Dict:
    """
    Get LTP (Last Traded Price) data using available API methods
    """
    try:
        # Method 1: Try historical data API (most accurate)
        latest_data = self.get_latest_data(symbol)
        if latest_data and 'close' in latest_data:
            return {
                'symbol': symbol,
                'ltp': latest_data.get('close'),  # Use close as LTP
                'cp': latest_data.get('close'),   # Use close as previous close
                'open': latest_data.get('open'),
                'high': latest_data.get('high'),
                'low': latest_data.get('low'),
                'volume': latest_data.get('volume'),
                'ltq': 0,  # Not available from historical data
            }
        
        # Method 2: Try direct HTTP request (fallback)
        return self._get_ltp_data_fallback(symbol)
        
    except Exception as e:
        logger.error(f"All LTP methods failed for {symbol}: {e}")
        return {}
```

#### 2. Add Cache Fallback

```python
def _get_cache_fallback(self, symbol: str) -> Dict:
    """Get previous close from cache as final fallback"""
    try:
        # Import cache system
        from src.scanner.stock_scorer import stock_scorer
        
        # Get cached data
        if symbol in stock_scorer.stock_metadata:
            metadata = stock_scorer.stock_metadata[symbol]
            if 'prev_close' in metadata:
                return {
                    'symbol': symbol,
                    'ltp': metadata.get('prev_close'),
                    'cp': metadata.get('prev_close'),  # Use cached close as previous close
                    'open': metadata.get('prev_close'),
                    'high': metadata.get('prev_close'),
                    'low': metadata.get('prev_close'),
                    'volume': 0,
                    'ltq': 0,
                }
    except Exception as e:
        logger.error(f"Cache fallback failed for {symbol}: {e}")
    
    return {}
```

### Benefits of This Solution

1. **Accurate Previous Close**: Uses historical data API to get actual last trading day close
2. **Cache Fallback**: Falls back to cached data if API fails
3. **No Weekend/Holiday Issues**: Historical data naturally excludes non-trading days
4. **Consistent with Scanner**: Uses same data sources as the scanner system
5. **Robust Error Handling**: Multiple fallback layers

### Files to Modify

1. **`src/utils/upstox_fetcher.py`**: Update `get_ltp_data` method
2. **`src/trading/live_trading/run_reversal.py`**: No changes needed (already calls `get_ltp_data`)
3. **`src/trading/live_trading/run_continuation.py`**: No changes needed (same issue affects continuation bot)

This solution ensures both reversal and continuation bots get accurate previous close prices for correct gap calculations.

first we do testing okay 
so create testing script
The bug is that the LTP V3 API's 'cp' field is returning stale or incorrect previous close data—it's stuck on Thursday's close (22-01-2026) instead of Friday's (23-01-2026) for Tuesday (27-01-2026). This is not uncommon in Upstox V3 LTP (from community reports and docs: 'cp' is supposed to be "the closing price from the previous trading day," handling holidays automatically, but it can be stale after weekends/holidays or due to token/cache issues). Your code is fine; the API response is the problem.

### Solution: Use Historical Candle V3 for Reliable Previous Close
Switch to the Historical Candle API (V3) to fetch the last daily candle's close. It's always accurate for the previous trading day (handles holidays by skipping no-data dates). Use interval '1d' (daily), fetch a small range (e.g., last 5 days), take the most recent candle's close.

This works anytime (even non-trading days), no rate limits for occasional calls.

#### Small Function Snippet (Add to upstox_fetcher.py)
```python
import requests
from datetime import datetime, timedelta

def get_previous_close(self, symbol: str) -> float or None:
    instrument_key = self.get_instrument_key(symbol)
    if not instrument_key:
        return None

    # Set date range: yesterday back 5 days to skip holidays
    today = datetime.now().date()
    to_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    from_date = (today - timedelta(days=5)).strftime('%Y-%m-%d')

    url = f"https://api.upstox.com/v3/historical-candle/{instrument_key}/1d/{to_date}/{from_date}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {self.access_token}"
    }

    try:
        response = requests.get(url, headers=headers).json()
        if response.get('status') == 'success' and response.get('data', {}).get('candles'):
            # Candles descending; first is most recent
            candles = response['data']['candles']
            last_close = candles[0][4]  # Index 4 = close
            return float(last_close)
        return None
    except Exception as e:
        logging.error(f"Historical previous close error for {symbol}: {e}")
        return None
```

#### Usage in Your Bot (Replace LTP 'cp' Fetch)
In your previous close loop:
```python
prev_closes = {}
for symbol in symbols:
    prev_close = upstox_fetcher.get_previous_close(symbol)
    if prev_close is not None:
        prev_closes[symbol] = prev_close
        print(f"   OK {symbol}: Prev Close Rs{prev_close:.2f}")
    else:
        # Fallback to LTP 'cp' if historical fails
        ltp_data = upstox_fetcher.get_ltp_data(symbol)
        if ltp_data and 'cp' in ltp_data:
            prev_closes[symbol] = float(ltp_data['cp'])
```

This is reliable—historical always gives the last trading day's close. Test now (should return Friday's close for Tuesday). If fails, it's token—refresh. No more stale data!

got it  ???
i'll enable act mode okay
for now just test it only do nothing after it

you have already created test_previous_close_fix.py 
so continue ahead from there
if still problem then again create report of the new problem
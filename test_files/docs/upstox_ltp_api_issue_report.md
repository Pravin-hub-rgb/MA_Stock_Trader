# Upstox LTP API Issue Report - Previous Close Data Problem

## Issue Summary
The Upstox LTP Quotes V3 API is not returning the expected `'cp'` (previous close) field. All LTP response fields are returning `None`, making it impossible to get accurate previous trading day close prices for gap calculations.

## Expected Behavior (per Expert Recommendation)
- LTP API should return `'cp'` field with previous trading day's close price
- This field should be reliable for NSE/BSE stocks and handle market holidays
- Used for accurate gap-up validation in live trading

## Actual Behavior
```python
# LTP API Response
{'symbol': 'BSE', 'ltp': None, 'cp': None, 'open': None, 'high': None, 'low': None, 'volume': None, 'timestamp': None}
```

## Implementation Details

### Code Changes Made
1. **Added `get_ltp_data()` method** in `upstox_fetcher.py`:
```python
def get_ltp_data(self, symbol: str) -> Dict:
    from upstox_client.api import MarketQuoteApi
    ltp_api = MarketQuoteApi(self.api_client)
    response = ltp_api.ltp(api_version='2.0', symbol=f"{instrument_key}")
    # Extract 'cp' field from response
```

2. **Modified live trading bot** to use LTP API instead of historical data:
```python
def get_previous_closes(self, symbols: List[str]) -> Dict[str, float]:
    ltp_data = self.upstox_fetcher.get_ltp_data(symbol)
    if ltp_data and 'cp' in ltp_data:
        prev_closes[symbol] = float(ltp_data['cp'])  # Using 'cp' field
```

### Test Results
- **Symbol Tested**: BSE
- **Expected Previous Close**: ₹2744.90 (January 7, 2026)
- **API Response**: All fields `None`
- **Error**: `float() argument must be a string or a real number, not 'NoneType'`

## Root Cause Analysis

### Possible Issues:
1. **API Authentication**: LTP API may require different permissions than historical data
2. **API Version**: Using `api_version='2.0'` - may need different version
3. **Instrument Key Format**: Using `NSE_EQ|BSE` format - may need different format
4. **Market Hours**: LTP API may not work outside market hours
5. **API Limits**: Rate limiting or subscription restrictions

### Verification Steps Taken:
1. ✅ Upstox client initializes successfully
2. ✅ Historical data API works (for comparison)
3. ✅ Instrument key resolution works
4. ❌ LTP API returns `None` for all fields

## Alternative Solutions Considered

### Option 1: Historical Candle API (Fallback)
```python
# Use 1-day historical candle as expert suggested
response = self.history_api.get_historical_candle_data(
    instrument_key=instrument_key,
    interval='day',
    to_date=today_str,
    from_date=week_ago_str
)
# Take the last candle's close as previous close
```

### Option 2: WebSocket Data
Extract `'cp'` from Market Data Feed V3 WebSocket stream when ticks arrive.

### Option 3: Official NSE API
Direct integration with NSE's official data sources for previous close verification.

## Impact on Live Trading
- **Critical**: Cannot perform accurate gap-up calculations
- **Risk**: Wrong previous close data leads to incorrect trading signals
- **Blocker**: System cannot go live until resolved

## Requested Expert Assistance

### Questions for Upstox Support:
1. Why is LTP Quotes V3 API returning `None` for all fields?
2. What are the correct API parameters for NSE stocks?
3. Is `'cp'` field available in current API version?
4. Are there subscription/permission requirements for LTP API?

### Test Case:
- Symbol: BSE
- Expected: `'cp'` field with value ~₹2744.90
- Actual: `'cp': None`

## Temporary Workaround
Until LTP API is fixed, consider using historical candle data as fallback:
```python
# Get last 2 days of daily candles
# Previous close = second-to-last candle's close price
```

## Files Modified
- `src/utils/upstox_fetcher.py` - Added `get_ltp_data()` method
- `src/trading/live_trading/main.py` - Modified to use LTP API
- `test_bse_upstox_method.py` - Test script demonstrating the issue

## Next Steps
1. Share this report with Upstox API expert
2. Get clarification on LTP API usage
3. Implement working solution
4. Re-test with BSE and other symbols
5. Verify gap calculations work correctly

---
**Status**: BLOCKED - Cannot proceed with live trading until LTP API issue is resolved
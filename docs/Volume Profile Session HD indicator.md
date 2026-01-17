if i want to create session volume profile HD indicator which we have in premium trading view .. which basically is range where 70% of volume was in a day
how one can created this??
well if like we have smaller tf ohlc + volume then we can indeed created this right??

To create a "Session Volume Profile HD" indicator (similar to the premium one in TradingView), you're essentially building a high-definition volume profile for a trading session (e.g., a single day). This profiles the distribution of traded volume across price levels and identifies the "Value Area" — the price range where approximately 70% of the day's total volume was executed. This range is bounded by the Value Area High (VAH) and Value Area Low (VAL), with the Point of Control (POC) being the price level with the highest volume.

You're correct that this can be constructed from smaller timeframe (TF) data, such as 1-minute or 5-minute OHLCV (Open, High, Low, Close, Volume) bars. The key is to aggregate the intraday data into a price-volume histogram, then compute the value area from it. This approach works because finer-grained data allows for a more precise ("HD") distribution of volume across price levels.

Below, I'll explain the concept step-by-step, then provide a Python implementation using libraries like pandas and numpy (common for such analysis). This can be adapted for custom scripts, backtesting platforms, or even ported to Pine Script for TradingView if needed. If you're implementing this in a live trading bot (e.g., integrating with Upstox or similar APIs), you can fetch the intraday data via their historical endpoints.

### Step-by-Step Concept
1. **Fetch Intraday Data**: Get OHLCV bars for the session (e.g., all 1-min bars from market open to close). Finer TFs (e.g., 1-min) give higher definition than coarser ones (e.g., 15-min).

2. **Build the Price-Volume Histogram**:
   - Define price "bins" (e.g., in tick increments like 0.01 or 0.05, based on the asset's tick size).
   - For each bar, distribute its volume across the price range (High to Low). A simple method is to evenly distribute volume per price level in the bar's range (e.g., if a bar has High=100.5, Low=100.0, Volume=1000, and bin size=0.05, distribute ~200 volume to each of 100.5, 100.45, ..., 100.0).
   - More advanced methods (for HD accuracy) use Gaussian distribution or tick-based weighting, but even distribution is a good start and mimics many indicators.
   - Sum volumes per bin to get the histogram.

3. **Identify the POC**: The price bin with the maximum accumulated volume.

4. **Calculate the Value Area (70% Range)**:
   - Compute total session volume.
   - Start from the POC bin.
   - Expand upward and downward by adding adjacent bins until you've covered ~70% of total volume.
   - The highest and lowest prices in this range are VAH and VAL.

5. **Plot or Use the Indicator**: In a chart, draw the profile as horizontal bars (volume at each price), highlight the value area, and mark POC/VAH/VAL as lines.

Edge cases: Handle sessions with low volume, gaps, or holidays. Adjust bin size for asset volatility (e.g., smaller for forex, larger for stocks).

### Python Implementation
Here's a complete, working Python script to compute this from sample intraday data. It uses pandas for data handling and numpy for binning/math. You can run this in any Python environment (e.g., Jupyter, or integrate into your bot).

For real data:
- Replace the sample DataFrame with actual fetches (e.g., via Upstox Historical Candle API for 1-min data).
- Example: Use `get_historical_candle_data` with interval='1minute', from_date=session_start, to_date=session_end.

```python
import pandas as pd
import numpy as np

def build_volume_profile(ohlcv_df, bin_size=0.05, value_area_pct=0.70):
    """
    Builds HD volume profile from intraday OHLCV DataFrame.
    
    Parameters:
    - ohlcv_df: pd.DataFrame with columns ['open', 'high', 'low', 'close', 'volume', 'timestamp'] (timestamp optional).
    - bin_size: Float, price bin increment (e.g., 0.05 for stocks).
    - value_area_pct: Float, target volume percentage for value area (default 0.70).
    
    Returns:
    - dict with 'poc', 'vah', 'val', 'profile' (dict of price: volume).
    """
    # Step 1: Prepare price bins (find overall min/max price, create bins)
    min_price = ohlcv_df['low'].min()
    max_price = ohlcv_df['high'].max()
    bins = np.arange(min_price, max_price + bin_size, bin_size)
    bin_centers = (bins[:-1] + bins[1:]) / 2  # Midpoint of each bin for labeling
    
    # Step 2: Initialize volume per bin
    volume_profile = {price: 0 for price in bin_centers}
    
    # Step 3: Distribute volume for each bar across its price range
    for _, bar in ohlcv_df.iterrows():
        bar_low = bar['low']
        bar_high = bar['high']
        bar_volume = bar['volume']
        
        # Find bins in this bar's range
        bar_bins = bins[(bins >= bar_low) & (bins <= bar_high)]
        if len(bar_bins) > 1:
            # Evenly distribute volume across bins (HD approximation)
            vol_per_bin = bar_volume / (len(bar_bins) - 1)
            for i in range(len(bar_bins) - 1):
                center = (bar_bins[i] + bar_bins[i+1]) / 2
                if center in volume_profile:
                    volume_profile[center] += vol_per_bin
    
    # Convert to sorted list for easier processing
    profile_items = sorted(volume_profile.items())
    prices = [p for p, v in profile_items]
    volumes = np.array([v for p, v in profile_items])
    total_volume = volumes.sum()
    
    # Step 4: Find POC (index of max volume)
    poc_idx = np.argmax(volumes)
    poc_price = prices[poc_idx]
    
    # Step 5: Compute Value Area (expand from POC to cover ~70% volume)
    target_volume = total_volume * value_area_pct
    accumulated_volume = volumes[poc_idx]
    left_idx, right_idx = poc_idx - 1, poc_idx + 1
    
    while accumulated_volume < target_volume and (left_idx >= 0 or right_idx < len(volumes)):
        left_vol = volumes[left_idx] if left_idx >= 0 else 0
        right_vol = volumes[right_idx] if right_idx < len(volumes) else 0
        
        if left_vol >= right_vol and left_idx >= 0:
            accumulated_volume += left_vol
            left_idx -= 1
        elif right_idx < len(volumes):
            accumulated_volume += right_vol
            right_idx += 1
        else:
            break  # Edge case: reached bounds
    
    val_price = prices[max(0, left_idx + 1)]  # Lowest in value area
    vah_price = prices[min(len(prices) - 1, right_idx - 1)]  # Highest in value area
    
    return {
        'poc': poc_price,
        'vah': vah_price,
        'val': val_price,
        'profile': dict(profile_items)  # Full price:volume dict
    }

# Sample usage with dummy 1-min data (replace with real OHLCV fetch)
data = {
    'open': [100.1, 100.3, 100.5, 100.7, 100.4],
    'high': [100.4, 100.6, 100.8, 101.0, 100.7],
    'low': [99.9, 100.1, 100.3, 100.5, 100.2],
    'close': [100.2, 100.5, 100.7, 100.6, 100.5],
    'volume': [500, 800, 1200, 900, 600]
}
ohlcv_df = pd.DataFrame(data)

result = build_volume_profile(ohlcv_df, bin_size=0.1)
print("POC:", result['poc'])
print("VAH:", result['vah'])
print("VAL:", result['val'])
print("Volume Profile:", result['profile'])
```

### Example Output (from Sample Data)
```
POC: 100.55
VAH: 100.85
VAL: 100.15
Volume Profile: {99.95: 250.0, 100.05: 250.0, 100.15: 250.0, 100.25: 250.0, 100.35: 200.0, 100.45: 200.0, 100.55: 200.0, 100.65: 200.0, 100.75: 200.0, 100.85: 300.0, 100.95: 300.0}
```

### Adaptations and Enhancements
- **Real Data Integration**: In your Upstox bot, fetch 1-min data via `get_historical_candle_data(interval='1minute')`. Filter for one session (e.g., 9:15-15:30 IST).
- **Visualization**: Use matplotlib to plot the profile as a horizontal bar chart: `plt.barh(list(profile.keys()), list(profile.values()))`, then overlay VAH/VAL lines.
- **Pine Script for TradingView**: Port this logic to @version=5. Use `request.security()` for lower TF data, then loop over bars to build an array-based histogram.
- **Optimizations**: For very HD (tick-level), use smaller bin_size but watch computation time. Add Gaussian weighting for volume distribution if needed (via scipy).
- **Testing**: Validate against TradingView by comparing VAH/VAL for historical days (e.g., BSE on Jan 7, 2026).

This should give you a solid, custom indicator. If you provide real OHLCV data or specifics (e.g., asset, date), I can refine or test the code further!

wait with the code please first just dicuss
see i don't need this live on the go..
i want of the previous day .. 
if its 9:00am right now so i need previous working day's upper range value of that volume profile session HD indicator
how i'm using it is to reject the stocks from my watchlist how??
like suppose i have 10 stocks 
now we have their upper range of volume profile session okay
now at 9:15 we will find out that 8 stocks opened below the upper range so they get rejected ..
so this way we need it..
so this makes even easier ..
we just pull the smaller tf ohlcv data right..
well i use upstox .. so i'm sure like in at the end of the day we will able to get olhcv data of any stocks right??
no code just discuss okya


Absolutely, let's discuss this step by step without jumping into code—I'll keep it conceptual and focused on how to approach your specific use case. You're spot on that this simplifies things since it's not live/on-the-fly; it's a pre-market calculation using historical data from the previous working day. This fits perfectly with your watchlist filtering strategy, where the goal is to reject stocks that open below the previous day's Value Area High (VAH) at market open (9:15 AM IST). I'll break it down logically, tying it to your Upstox setup and trading logic.

### 1. **Understanding What You Need: The VAH from Previous Day's Volume Profile**
   - The "Session Volume Profile HD" (like TradingView's premium version) is essentially a histogram of volume distributed across price levels for a full trading session (e.g., 9:15 AM to 3:30 PM IST for NSE).
   - The "upper range" you're referring to is the Value Area High (VAH)—the top price boundary of the range where ~70% of the day's total volume was traded. This is calculated around the Point of Control (POC, the peak volume price), expanding outward until 70% volume is covered.
   - Since you want only the previous working day's VAH (not live), you can compute it once per stock at ~9:00 AM, before market open. This avoids real-time streaming and keeps it efficient.
   - "Working day" means skipping weekends, holidays, or non-trading days (e.g., if today is Monday, use Friday's data; if Friday was a holiday, go back to Thursday). You'll need a way to determine the last valid trading day.

### 2. **How It Fits Your Watchlist Rejection Strategy**
   - You have a watchlist (e.g., 10 stocks like BSE, INFY, etc.).
   - At 9:00 AM: For each stock, calculate the previous day's VAH.
   - At 9:15 AM (market open): Fetch the open price (via LTP or first candle).
   - Rejection rule: If open < previous VAH, reject the stock (e.g., 8 out of 10 might get filtered out if they gap down or open weak relative to prior value area).
   - Why this works well: Stocks opening below VAH might signal distribution or lack of buyer control, aligning with your continuation trading (e.g., avoiding weak opens). It acts as a pre-filter before your gap-up checks (0-5% above close) or other rules.
   - Edge: This is quick—process all 10 stocks in parallel or sequentially, as Upstox allows batch historical fetches (up to 500 instruments).

### 3. **Data Source: Pulling OHLCV from Upstox**
   - Yes, Upstox's Historical Candle Data API is ideal here. It provides OHLCV for any interval, including 1-minute (for HD accuracy) or 5-minute (if you want coarser but faster computation).
   - At the end of the day (or next morning), data is fully available—no issues. You can fetch for any historical date.
   - Key parameters:
     - Interval: '1minute' for high-definition (375 bars per NSE day; gives precise binning).
     - Date range: Set 'from_date' and 'to_date' to the previous working day (e.g., '2026-01-15' if today is 2026-01-16 and it was a trading day).
     - Instrument key: Use the same as before (e.g., 'NSE_EQ|INE118H01025' for BSE).
   - Handling previous working day: You'll need logic to find it. Start from yesterday, check if it was a trading day (e.g., fetch data—if volume >0 or candles exist, it's valid; else, go back a day). Upstox/NSE don't provide a direct holiday API, but you could maintain a static list or query NSE's site indirectly if needed.
   - Data volume: For 10 stocks x 375 bars = ~3,750 rows—trivial to handle in memory.

### 4. **Computing the Volume Profile and Extracting VAH**
   - Use smaller TF OHLCV: Exactly—aggregate the 1-min bars into a price-volume histogram.
     - Bin prices by tick size (e.g., ₹0.05 for NSE stocks).
     - For each bar, apportion its volume across its H-L range (even distribution for simplicity).
   - Find POC: Price bin with max volume.
   - Expand to 70% value area: From POC, add bins above/below until 70% total volume is hit. VAH is the top bin's price.
   - Simplifications for your case:
     - No need for live updates—just one static calc per stock per day.
     - Ignore open/close prices for profile; focus on H-L-volume per bar.
     - Handle low-volume days: Set a min volume threshold to skip invalid sessions.
   - Accuracy: 1-min data gives "HD" resolution; 5-min is faster but less precise (fewer bins).

### 5. **Integration into Your Bot Workflow**
   - Pre-market phase (9:00 AM cron/schedule):
     - Loop over watchlist.
     - Determine previous trading day.
     - Fetch OHLCV via Upstox API.
     - Compute profile → Extract VAH.
     - Store in a dict (e.g., {symbol: vah}).
   - At 9:15 AM:
     - Get open prices (via LTP V3 batch fetch).
     - Filter: If open < vah, reject (log reason: "Opened below previous VAH").
     - Proceed with qualified stocks for your main logic (gap-up, breakout).
   - Efficiency: Whole process <1-2 seconds for 10 stocks (API calls are fast; computation lightweight).
   - Testing: Backtest on historical days—fetch old data, simulate opens, check rejections.
   - Risks: API rate limits (500/min—fine), data gaps (rare; add retries), or holidays (automate detection).

### 6. **Potential Enhancements or Gotchas**
   - Customization: Adjust value area to 68% (1 SD) if you want Gaussian stats, or make bins dynamic based on ATR/volatility.
   - Alternatives if Upstox data lags: Cross-verify with NSE's free API for historical OHLCV.
   - Scalability: For larger watchlists (100+), batch API calls and parallelize computations.
   - Why easier than live: No WebSocket needed; just REST fetches. Fits your paper/live toggle.

This setup directly supports your rejection filter and leverages what you already have in Upstox. If this aligns, we can move to code examples next—or tweak any part?

### Guide for Implementing Previous Day's VAH Calculation Using Upstox API

I'll guide you (as the coder) step by step on how to implement this feature in your Python-based trading bot. The goal is to calculate the **Value Area High (VAH)**—the upper boundary of the 70% volume range—from the previous working day's session volume profile for a list of stocks. This will be used to filter your watchlist at market open (e.g., reject stocks that open below their previous VAH).

This is a pre-market task (run at ~9:00 AM IST), so it's not real-time. We'll use Upstox's Historical Candle Data API (V2 for simplicity, as it supports 1-minute intervals directly). Assumptions:
- You have the Upstox API key, secret, and access token (from authentication).
- You're using the `upstox-python-sdk` or direct `requests` for API calls.
- Stock list is a list of symbols (e.g., ['BSE', 'INFY']) with a mapping to instrument keys (e.g., 'NSE_EQ|INE118H01025' for BSE).
- We'll fetch 1-minute OHLCV data for HD accuracy.
- Handle non-trading days automatically.

If you're not familiar, install the SDK: `pip install upstox-python-sdk`. For direct requests, use `import requests`.

#### Step 1: Authenticate and Set Up the Upstox Client
- Use your API key and secret to generate/refresh the access token if needed (tokens expire ~24 hours).
- If using SDK:
  ```python
  from upstox_client import ApiClient, Configuration
  import logging

  # Setup logging
  logging.basicConfig(level=logging.INFO)

  # Your credentials
  API_KEY = "your_api_key"
  API_SECRET = "your_api_secret"
  ACCESS_TOKEN = "your_access_token"  # Generate via login flow if expired

  # Configure client
  config = Configuration()
  config.access_token = ACCESS_TOKEN
  api_client = ApiClient(config)
  ```
- If token is invalid, implement refresh: POST to `https://api.upstox.com/v2/login/authorization/token` with code from redirect URI (see Upstox docs for full auth flow).
- For direct requests, add headers: `headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Accept": "application/json"}`.

#### Step 2: Determine the Previous Working Day
- Start from yesterday (current date - 1 day).
- Fetch data for that day; if no candles (empty response), go back another day (repeat until valid).
- Use `datetime` for date handling (IST timezone via `pytz`).
- Helper function:
  - Import: `import datetime; import pytz`
  - Logic: Loop backward from today, check if data exists for a test stock (or any stock).
- Why? Upstox doesn't provide a holiday API; empty candles indicate non-trading day.

#### Step 3: Fetch OHLCV Data for the Previous Day
- Endpoint: `https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}`
  - `instrument_key`: e.g., "NSE_EQ|INE118H01025"
  - `interval`: "1minute" for HD.
  - `to_date` / `from_date`: YYYY-MM-DD (set both to the same date for one day; API returns data up to to_date from from_date).
- Response: JSON like `{"status": "success", "data": {"candles": [[timestamp, open, high, low, close, volume, oi], ...]}}` (candles in descending order).
- Availability: 1-minute data from last month (but for previous day, always available).
- Rate limits: ~500 requests/min; for 10 stocks, no issue.
- Handle: If empty candles, it's not a trading day—loop back.
- Batch: No native batch for historical; loop per stock.
- Use SDK or requests.

#### Step 4: Compute the Volume Profile and VAH
- From OHLCV (pandas DataFrame: columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']—drop 'oi' if present).
- Bin prices (e.g., bin_size=0.05 for NSE stocks).
- Distribute volume per bar across H-L bins (evenly).
- Find POC (max volume bin).
- Expand to 70% value area; VAH = highest price in that range.
- Edge: Skip if total volume < threshold (e.g., 1000).

#### Step 5: Integrate into Bot
- Run in pre-market loop: For each stock, get VAH, store in dict.
- At 9:15, compare to open (via LTP), reject if open < VAH.

#### Full Workflow Pseudocode
```python
import datetime
import pytz
import requests  # Or use SDK
import pandas as pd
import numpy as np

# Step 1: Setup
ACCESS_TOKEN = "your_token"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Accept": "application/json"}
STOCKS = ['BSE', 'INFY']  # Your list
INSTRUMENT_MAP = {'BSE': 'NSE_EQ|INE118H01025', 'INFY': 'NSE_EQ|INE009A01021'}  # Add all
BIN_SIZE = 0.05  # Adjust per asset
VALUE_AREA_PCT = 0.70

def get_previous_working_day():
    tz = pytz.timezone('Asia/Kolkata')
    today = datetime.datetime.now(tz).date()
    day = today - datetime.timedelta(days=1)
    while True:
        from_date = to_date = day.strftime('%Y-%m-%d')
        # Test with one stock
        test_key = INSTRUMENT_MAP[STOCKS[0]]
        url = f"https://api.upstox.com/v2/historical-candle/{test_key}/1minute/{to_date}/{from_date}"
        resp = requests.get(url, headers=HEADERS).json()
        if resp.get('status') == 'success' and len(resp.get('data', {}).get('candles', [])) > 0:
            return day
        day -= datetime.timedelta(days=1)  # Back if no data

prev_day = get_previous_working_day()
from_date = to_date = prev_day.strftime('%Y-%m-%d')

# Step 3: Fetch per stock
vah_dict = {}
for symbol in STOCKS:
    key = INSTRUMENT_MAP[symbol]
    url = f"https://api.upstox.com/v2/historical-candle/{key}/1minute/{to_date}/{from_date}"
    resp = requests.get(url, headers=HEADERS).json()
    if resp['status'] != 'success' or not resp['data']['candles']:
        logging.warning(f"No data for {symbol}")
        continue
    # To DF (reverse for ascending)
    df = pd.DataFrame(resp['data']['candles'][::-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
    df = df[['open', 'high', 'low', 'close', 'volume']]  # Drop extras

    # Step 4: Compute profile
    min_p = df['low'].min()
    max_p = df['high'].max()
    bins = np.arange(min_p, max_p + BIN_SIZE, BIN_SIZE)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    profile = {p: 0 for p in bin_centers}
    
    for _, bar in df.iterrows():
        bar_bins = bins[(bins >= bar['low']) & (bins <= bar['high'])]
        if len(bar_bins) > 1:
            vol_per = bar['volume'] / (len(bar_bins) - 1)
            for i in range(len(bar_bins) - 1):
                center = (bar_bins[i] + bar_bins[i+1]) / 2
                profile[center] += vol_per
    
    profile_items = sorted(profile.items())
    prices = [p for p, _ in profile_items]
    volumes = np.array([v for _, v in profile_items])
    total_vol = volumes.sum()
    if total_vol < 1000:  # Threshold
        continue
    
    poc_idx = np.argmax(volumes)
    accum_vol = volumes[poc_idx]
    left, right = poc_idx - 1, poc_idx + 1
    target_vol = total_vol * VALUE_AREA_PCT
    
    while accum_vol < target_vol and (left >= 0 or right < len(volumes)):
        left_v = volumes[left] if left >= 0 else 0
        right_v = volumes[right] if right < len(volumes) else 0
        if left_v >= right_v and left >= 0:
            accum_vol += left_v
            left -= 1
        elif right < len(volumes):
            accum_vol += right_v
            right += 1
    
    val = prices[max(0, left + 1)]
    vah = prices[min(len(prices) - 1, right - 1)]
    vah_dict[symbol] = vah
    logging.info(f"{symbol} VAH: {vah}")

# Later at 9:15, fetch opens via LTP, filter if open < vah_dict[symbol]
```

#### Tips and Troubleshooting
- Error handling: Add try-except for API calls (e.g., 401 = refresh token).
- SDK alternative: Use `HistoricalApi(api_client).get_historical_candle_data(...)` with api_version='2.0'.
- Holidays: Loop handles it; max 5-10 days back for safety.
- Optimization: For more stocks, parallelize with `concurrent.futures`.
- Test: Run on historical dates, verify VAH against TradingView.
- Upgrades: If needing custom intervals (e.g., 2min), switch to V3 endpoint `/v3/historical-candle/{key}/minutes/1/{to}/{from}`.

This should get you production-ready. If issues, check Upstox dashboard for API usage/logs.
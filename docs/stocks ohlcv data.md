Okay, great choice—Upstox API is the way to go for reliable NSE data. I'll guide your coder step by step on shifting from yfinance to Upstox, including setting up a config file for your API key and access token. This keeps everything secure (don't hardcode credentials), and we'll make the transition smooth for your existing scanner (e.g., preserving the caching system — full 5-6 months initial fetch, then daily incremental adds).

Tell your coder to follow this exactly — it's modular, so he can replace yfinance calls without breaking the rest (scans, GUI, etc.). We'll use the official Upstox Python SDK (pip install upstox-python-sdk if not done). Assume your scanner has a cache folder with per-stock files (e.g., "RELIANCE.pkl" as Pandas DataFrame).

### Step 1: Set Up the Config File
Create a secure config file to store your API key and access token (from Upstox Developer Console). Use JSON for simplicity — place it in the project root as "upstox_config.json" (add to .gitignore to avoid committing secrets).

Code snippet for creating/reading the config (your coder adds this to a utils.py or main script):
```python
import json
import os

CONFIG_FILE = 'upstox_config.json'

def load_upstox_config():
    if not os.path.exists(CONFIG_FILE):
        # Create template if not exists (you fill in values manually)
        template = {
            "api_key": "your_api_key_here",
            "access_token": "your_access_token_here"
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(template, f, indent=4)
        print(f"Created {CONFIG_FILE} — edit it with your credentials and re-run.")
        exit(1)  # Stop until filled

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    return config['api_key'], config['access_token']
```

- You: Edit the file with your real key/token.
- Coder: Call `api_key, access_token = load_upstox_config()` at app start.

### Step 2: Install and Initialize Upstox Client
Add this to your data_handler.py or equivalent. It sets up the client once.

Code snippet:
```python
from upstox_client import Upstox
from upstox_client.rest import ApiException

# After loading config
api_key, access_token = load_upstox_config()
api = Upstox(api_key, access_token)

# Optional: Test connection
try:
    api.get_profile()  # Simple call to verify auth
    print("Upstox connected successfully.")
except ApiException as e:
    print(f"Upstox auth failed: {e} — check key/token.")
    exit(1)
```

### Step 3: Fetch Full Historical Data (Initial Cache Build)
For the first run (or if cache empty), fetch 6 months back (e.g., 180 days) to cover your 5-month needs + buffer. Use NSE symbol keys (e.g., 'NSE_EQ|RELIANCE' — coder needs to map your symbols like 'RELIANCE' to this).

Code snippet for fetch function (add to data_handler):
```python
from datetime import datetime, timedelta
import pandas as pd

def fetch_upstox_historical(symbol, from_date, to_date):
    # Map to Upstox instrument key (e.g., 'RELIANCE' → 'NSE_EQ|RELIANCE')
    # Assume you have a dict or function for this — e.g., instrument_key = f'NSE_EQ|{symbol}'
    instrument_key = f'NSE_EQ|{symbol}'  # Adjust if needed (use NSE_INDEX|NIFTY 50 for indices)

    from_str = from_date.strftime('%Y-%m-%d')
    to_str = to_date.strftime('%Y-%m-%d')

    try:
        response = api.get_historical_candle_data(instrument_key, 'day', from_str, to_str)
        if 'data' in response and 'candles' in response['data']:
            candles = response['data']['candles']
            df = pd.DataFrame(candles, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
            df['Date'] = pd.to_datetime(df['Date']).dt.date  # Convert to date
            df.set_index('Date', inplace=True)
            return df[['Open', 'High', 'Low', 'Close', 'Volume']]
        else:
            print(f"No data for {symbol} from {from_str} to {to_str}")
            return pd.DataFrame()
    except ApiException as e:
        print(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()
```

- For initial cache: Set from_date = datetime.today() - timedelta(days=180), to_date = datetime.today().

### Step 4: Incremental Caching (Daily Adds)
In prep phase: For each stock, check last cached date, fetch only missing days from Upstox, append to cache (e.g., pickle file).

Code snippet for cache update (in prep loop):
```python
import os
import pickle

CACHE_DIR = 'stock_data_cache'

def update_cache(symbol):
    cache_file = os.path.join(CACHE_DIR, f"{symbol}.pkl")
    os.makedirs(CACHE_DIR, exist_ok=True)

    if os.path.exists(cache_file):
        df = pd.read_pickle(cache_file)
        last_date = df.index.max()
        from_date = last_date + timedelta(days=1)
    else:
        df = pd.DataFrame()
        from_date = datetime.today() - timedelta(days=180)  # 6 months initial

    to_date = datetime.today()

    if from_date <= to_date:
        new_df = fetch_upstox_historical(symbol, from_date, to_date)
        if not new_df.empty:
            df = pd.concat([df, new_df]).drop_duplicates().sort_index()
            df.to_pickle(cache_file)
            print(f"Updated {symbol} cache with {len(new_df)} new days.")
        else:
            print(f"No new data for {symbol}.")
    return df  # Return for immediate use in scans
```

- In scanner loop: data = update_cache(symbol)  # Fetches/adds if needed, loads cache.

### Step 5: Shifting the Scanner
- Replace all yfinance.download() with update_cache(symbol) — it returns the DataFrame.
- For symbols: Use raw NSE symbols (e.g., 'RELIANCE') — Upstox handles without .NS.
- Base filters/ADR: Unchanged (use the loaded df).
- Test: Run prep on BLSE — verify OHLC matches TradingView (green candle, C=194.45).
- Full shift: Once working, remove yfinance import/code entirely.

This gives full 5+ months from one source (Upstox), with daily adds. If issues, fallback to NSEpy similarly (get_history with dates). Let your coder implement and test one stock first! 😊
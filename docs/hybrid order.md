### Quick Confirmation on Dhan's Free API
Yep, spot on—Dhan's free core APIs (orders, positions, holdings via REST) don't include real-time tick data (LTP/volume updates) for stocks *or* options. That's locked behind their ₹499/month Data API subscription (WebSocket feeds). For your NSE stock swings, the hybrid (Upstox data + Dhan execution) dodges that entirely—zero extra costs.

---

# Hybrid Trading Bot Documentation: Upstox Data Analysis + Dhan Order Execution for NSE Stock Swings

## Overview
This guide outlines a **hybrid API setup** for a swing trading bot targeting NSE equities (e.g., RELIANCE, TATAMOTORS). It leverages:
- **Upstox's free WebSocket V3** for real-time tick data (LTP, volume, OHLC every ~1 second—sufficient for swing signals like EMA crossovers or volume breakouts).
- **Dhan's free REST API** for order placement/execution (zero delivery brokerage, saving ~0.02-0.05% per round-trip vs. Upstox on small positions like your ₹10k examples).

**Why Hybrid?**
- Prices are identical (single NSE feed), so no slippage risk.
- Total latency: <200ms (Upstox tick → analysis → Dhan order).
- Cost: ₹0 upfront; only standard brokerage (~₹0 for delivery buys/sells on Dhan) + statutory fees (~0.23% round-trip).
- Ideal for swings: Hold days/weeks, enter on signals (e.g., 9:15 AM breakout with SL calc).

**Assumptions**:
- You have active Upstox and Dhan accounts (funded for live; use paper trading first).
- Python 3.10+ environment with `requests`, `websocket-client`, `pandas` (for analysis).
- Bot logic: Risk-based sizing (e.g., ₹300 risk → qty = risk / (entry - SL) * min lot 1 for stocks).
- Test in sim mode before live.

**Pros/Cons Table**:
| Aspect | Pros | Cons |
|--------|------|------|
| **Cost** | Free data/orders; Dhan's zero delivery brokerage. | Minor brokerage parity on large trades (both ~₹0). |
| **Data Quality** | Upstox: Reliable ~1s ticks for 100+ stocks; full OHLC. | Not true sub-second ticks (fine for swings, not HFT). |
| **Execution** | Dhan: <50ms orders; GTT/SL support for swings. | Cross-broker auth adds 1-2 lines of code. |
| **Scalability** | Up to 5k subs on Upstox; 25 orders/sec on Dhan. | Manual position sync (poll Dhan API post-order). |

**Legal Note**: This is for educational use. Comply with SEBI regs (no auto-trading without approval if >₹10L turnover). Backtest thoroughly.

## Prerequisites
1. **API Keys**:
   - **Upstox**: Log in to Upstox Developer Console (developer.upstox.com) → Create app (select "Trading + Data") → Get `api_key`, `api_secret`. Generate access token daily via `/login/authorization` (OAuth flow).
   - **Dhan**: DhanHQ dashboard (hqdhan.com) → API section → Generate client ID & secret. Get access token via `/auth` endpoint (valid 24h).

2. **Libraries**:
   ```bash
   pip install websocket-client requests pandas numpy
   ```

3. **Paper Trading**:
   - Upstox: Enable in app settings.
   - Dhan: Use sandbox endpoints (e.g., `https://sandbox.dhan.co`).

## Step-by-Step Setup
### 1. Authenticate Both APIs
Handle tokens in a config file or env vars. Upstox needs daily refresh; Dhan's lasts 24h.

**Sample Code: `auth.py`** (Run once per session)
```python
import requests
import os
from datetime import datetime

# Upstox Config
U_API_KEY = os.getenv('UPSTOX_API_KEY')  # Your api_key
U_API_SECRET = os.getenv('UPSTOX_API_SECRET')  # Your api_secret
U_ACCESS_TOKEN = None  # Will fetch

def get_upstox_token():
    # Step 1: Get request token (manual login first via browser for code challenge)
    # Visit: https://api.upstox.com/v2/login/authorization?response_type=code&client_id={U_API_KEY}&redirect_uri=https://upstox.com
    # Extract 'code' from redirect URL, then:
    code = input("Paste the 'code' from redirect: ")  # Automate with Selenium if needed
    url = "https://api.upstox.com/v2/login/authorization/token"
    data = {
        'code': code,
        'client_id': U_API_KEY,
        'client_secret': U_API_SECRET,
        'redirect_uri': 'https://upstox.com',
        'grant_type': 'authorization_code'
    }
    resp = requests.post(url, data=data)
    if resp.status_code == 200:
        U_ACCESS_TOKEN = resp.json()['access_token']
        print(f"Upstox Token: {U_ACCESS_TOKEN}")
        return U_ACCESS_TOKEN
    else:
        raise ValueError("Upstox auth failed")

# Dhan Config
D_CLIENT_ID = os.getenv('DHAN_CLIENT_ID')
D_CLIENT_SECRET = os.getenv('DHAN_CLIENT_SECRET')
D_ACCESS_TOKEN = None

def get_dhan_token():
    url = "https://api.dhan.co/charts/v2/auth"
    data = {
        'client_id': D_CLIENT_ID,
        'client_secret': D_CLIENT_SECRET,
        'response_type': 'code'
    }
    # Similar: Get code via browser redirect to https://dhan.co, then exchange
    code = input("Paste Dhan 'code' from redirect: ")
    resp = requests.post(url, data={'code': code, 'grant_type': 'authorization_code'})
    if resp.status_code == 200:
        D_ACCESS_TOKEN = resp.json()['access_token']
        print(f"Dhan Token: {D_ACCESS_TOKEN}")
        return D_ACCESS_TOKEN
    else:
        raise ValueError("Dhan auth failed")

# Usage
if __name__ == "__main__":
    get_upstox_token()
    get_dhan_token()
```

### 2. Fetch Tick Data from Upstox
Subscribe to NSE stocks (e.g., "NSE_EQ|RELIANCE"). Get LTP/volume for analysis.

**Sample Code: `upstox_data.py`**
```python
import websocket
import json
import threading
from auth import U_ACCESS_TOKEN

TICKS = {}  # Dict: {symbol: {'ltp': float, 'volume': int, 'timestamp': str}}

def on_message(ws, message):
    data = json.loads(message)
    if 'data' in data and 'feed' in data['data']:
        for feed in data['data']['feed']:
            symbol = feed['instrumentToken']  # e.g., for RELIANCE
            TICKS[symbol] = {
                'ltp': float(feed['ltp']),
                'volume': int(feed['volume']),
                'timestamp': feed['exchangeTimestamp']
            }
            print(f"Tick: {symbol} LTP={feed['ltp']}, Vol={feed['volume']}")

def start_upstox_ws():
    ws_url = f"wss://ws.upstox.com/v3/marketfeed?access_token={U_ACCESS_TOKEN}"
    ws = websocket.WebSocketApp(ws_url, on_message=on_message)
    # Subscribe payload (JSON)
    sub_payload = {
        "guid": "some-guid",
        "method": "sub",
        "data": {
            "mode": "full",  # LTP + OHLC + depth
            "instrumentKeys": ["NSE_EQ|INE002A01018"]  # RELIANCE token; get from /instruments
        }
    }
    def on_open(ws):
        ws.send(json.dumps(sub_payload))
    ws.on_open = on_open
    ws.run_forever()

# Run in thread
if __name__ == "__main__":
    threading.Thread(target=start_upstox_ws, daemon=True).start()
    # Keep alive
    import time
    while True:
        time.sleep(1)
        print(TICKS)  # Your analysis here
```

**Get Instrument Tokens**: Call Upstox `/instruments` endpoint (free) to map symbols like "RELIANCE" to tokens.

### 3. Run Analysis & Calc Position Size
Use ticks for signals (e.g., LTP > 20-period EMA + volume > avg). Calc qty for ₹300 risk.

**Sample Code: `analysis.py`** (Integrate with above)
```python
import pandas as pd
import numpy as np
from upstox_data import TICKS

def calc_position_size(risk_amount=300, entry_ltp=2500, sl_ltp=2450):
    risk_per_share = abs(entry_ltp - sl_ltp)
    qty = int(risk_amount / risk_per_share)  # Min 1 share for stocks
    return qty

def analyze_signal(symbol='RELIANCE'):
    if symbol not in TICKS:
        return None
    ltp = TICKS[symbol]['ltp']
    # Simple EMA crossover (use pandas on historical ticks buffer)
    # Assume you buffer 20 ticks for EMA
    if ltp > 2500 and TICKS[symbol]['volume'] > 1000000:  # Example breakout
        sl = ltp * 0.98  # 2% SL
        qty = calc_position_size(entry_ltp=ltp, sl_ltp=sl)
        return {'action': 'BUY', 'symbol': symbol, 'qty': qty, 'price': ltp, 'sl': sl}
    return None

# Poll every 5s for swings
import time
while True:
    signal = analyze_signal()
    if signal:
        print(f"Signal: {signal}")
        # Trigger Dhan order
        break
    time.sleep(5)
```

### 4. Execute Orders on Dhan
POST to place CNC (delivery) orders with SL via GTT or bracket.

**Sample Code: `dhan_execution.py`**
```python
import requests
from auth import D_ACCESS_TOKEN
from analysis import analyze_signal  # Or pass signal

def place_dhan_order(signal):
    url = "https://api.dhan.co/charts/v2/orders"
    headers = {'access-token': D_ACCESS_TOKEN, 'Content-Type': 'application/json'}
    # Get order params: symbol_token from Dhan /instruments (similar to Upstox)
    payload = {
        "dhanClientId": "your_client_id",  # From auth
        "securityId": "12345",  # Fetch via /instruments for symbol
        "exchangeSegment": "NSE",
        "transactionType": "BUY",
        "quantity": signal['qty'],
        "orderType": "LIMIT",  # Or "MARKET"
        "productType": "CNC",  # Delivery for swings
        "price": signal['price'],
        "disclosedQuantity": signal['qty'],
        "triggerPrice": signal['sl'],  # For SL-M if needed
        "afterMarketOrder": False
    }
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200:
        order_id = resp.json()['data']['orderId']
        print(f"Order Placed: ID={order_id}")
        return order_id
    else:
        print(f"Error: {resp.text}")
        return None

# Usage
signal = analyze_signal()  # From Upstox
if signal:
    place_dhan_order(signal)

# Monitor: Poll /positions every 30s
def get_positions():
    url = "https://api.dhan.co/charts/v2/positions"
    headers = {'access-token': D_ACCESS_TOKEN}
    resp = requests.get(url, headers=headers)
    return resp.json() if resp.status_code == 200 else None
```

### 5. Full Bot Integration & Monitoring
- **Main Script**: `bot.py` – Thread Upstox WS, loop analysis, trigger Dhan on signal. Add exit logic (e.g., target hit or EOD).
- **Error Handling**: Retry on 429 rates; log to file.
- **Backtesting**: Use Upstox historicals (free via `/historical-candle`—up to 1y data).
- **Risk Controls**: Max 1-2 open positions; daily P&L check via Dhan `/pnl`.

**Sample Full Flow**:
1. Auth both.
2. Start Upstox WS in thread.
3. Loop: Analyze ticks → If signal, place Dhan order → Poll positions until exit.
4. Exit: Sell via similar POST (action="SELL").

## Testing & Deployment
- **Sim Mode**: Upstox paper for data; Dhan sandbox for orders. Run 1 week on historicals.
- **Live Go**: Start with ₹10k positions. Monitor via Telegram alerts (add `python-telegram-bot`).
- **Common Pitfalls**: Token expiry (cron refresh); Instrument token mismatches (sync via APIs).
- **Costs Recap**: ~₹23 round-trip on ₹10k (Dhan delivery)—your ₹300 risk intact.

## Resources
- Upstox Docs: developer.upstox.com/docs
- Dhan Docs: dhanhq.co/docs
- Community: Reddit r/IndianStreetBets or TradingView scripts for signal inspo.

Hit me if you need code tweaks (e.g., EMA buffer) or a GitHub stub! What's your first stock target?
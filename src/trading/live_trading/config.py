"""
Live Trading Configuration
All trading parameters in one place for easy modification
"""

from datetime import time

# === MARKET TIMING ===
MARKET_OPEN = time(9, 15)            # Market open time
ENTRY_DECISION_TIME = time(9, 20)    # Entry decision time 

# Auto-calculated (don't modify)
PREP_END = time(MARKET_OPEN.hour, MARKET_OPEN.minute, max(0, MARKET_OPEN.second - 30))
CONFIRMATION_WINDOW = (ENTRY_DECISION_TIME.hour * 60 + ENTRY_DECISION_TIME.minute) - (MARKET_OPEN.hour * 60 + MARKET_OPEN.minute)
ENTRY_PREP_TIME = ENTRY_DECISION_TIME

# === TRADING PARAMETERS ===
MAX_STOCKS_TO_TRADE = 5        # Maximum stocks to trade per day

# Gap up conditions
GAP_UP_MIN = 0.0               # Minimum gap up % (above previous close)
GAP_UP_MAX = 0.05              # Maximum gap up % (5% max)

# Low violation
LOW_VIOLATION_PCT = 0.01       # 1% below opening price = reject

# Entry conditions
ENTRY_SL_PCT = 0.04            # 4% stop loss below entry high

# === FILE PATHS ===
CONTINUATION_LIST_FILE = "src/trading/continuation_list.txt"
REVERSAL_LIST_FILE = "src/trading/reversal_list.txt"
TRADE_LOG_DIR = "logs/trades"

# === UPSTOX CONFIG ===
UPSTOX_CONFIG_FILE = "upstox_config.json"
SUBSCRIPTION_MODE = "full"     # Full mode for OHLC + LTP

# === LOGGING ===
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# === PAPER TRADING ===
PAPER_TRADING = True          # Always true for now, switch to False for live

# === RECONNECTION ===
MAX_RETRIES = 3
RETRY_DELAY = 2               # Seconds

# === DEBUG ===
DEBUG_MODE = False
PRINT_TICKS = False           # Print every tick (verbose)

# === TESTING ===
TEST_MODE = False            # Enable test mode (bypasses market timing)
SIMULATE_OPENING_PRICES = False # Use simulated opening prices for testing

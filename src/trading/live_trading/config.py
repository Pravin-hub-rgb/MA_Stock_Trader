"""
Live Trading Configuration
All trading parameters in one place for easy modification
"""

from datetime import time

# === MARKET TIMING ===
MARKET_OPEN = time(20, 48)            # Market open time
ENTRY_DECISION_TIME = time(20, 52)    # Entry decision time

# Auto-calculated (don't modify)
from datetime import datetime, timedelta

# Calculate PREP_END as MARKET_OPEN minus 30 seconds
market_open_datetime = datetime.combine(datetime.today(), MARKET_OPEN)
prep_end_datetime = market_open_datetime - timedelta(seconds=30)
PREP_END = prep_end_datetime.time()
CONFIRMATION_WINDOW = (ENTRY_DECISION_TIME.hour * 60 + ENTRY_DECISION_TIME.minute) - (MARKET_OPEN.hour * 60 + MARKET_OPEN.minute)
ENTRY_PREP_TIME = ENTRY_DECISION_TIME

# === TRADING PARAMETERS ===
MAX_STOCKS_TO_TRADE = 2        # Maximum stocks to trade per day (matches reversal logic)

# Gap up conditions
GAP_UP_MIN = 0.002             # Minimum gap up % (above previous close) - 0.20% for SVRO strong start
GAP_UP_MAX = 0.05              # Maximum gap up % (5% max)

# Strong Start gap percentage (configurable for easy adjustment)
STRONG_START_GAP_PCT = 0.02    # 2.0% minimum gap up for Strong Start (can be changed to 1.5%, 2.1%, etc.)

# Low violation
LOW_VIOLATION_PCT = 0.01       # 1% below opening price = reject

# Entry conditions
ENTRY_SL_PCT = 0.04            # 4% stop loss below entry high

# === FILE PATHS ===
# Adjust paths based on current working directory
import os
if os.path.basename(os.getcwd()) == 'src':
    # Running from src directory (standalone)
    CONTINUATION_LIST_FILE = "trading/continuation_list.txt"
    REVERSAL_LIST_FILE = "trading/reversal_list.txt"
    TRADE_LOG_DIR = "../logs/trades"
else:
    # Running from project root (via server)
    CONTINUATION_LIST_FILE = "src/trading/continuation_list.txt"
    REVERSAL_LIST_FILE = "src/trading/reversal_list.txt"
    TRADE_LOG_DIR = "logs/trades"

# === UPSTOX CONFIG ===
UPSTOX_CONFIG_FILE = "upstox_config.json"
SUBSCRIPTION_MODE = "full"     # Full mode for OHLC + LTP

# === LOGGING ===
LOG_LEVEL = "DEBUG"
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
# (Removed - production only)

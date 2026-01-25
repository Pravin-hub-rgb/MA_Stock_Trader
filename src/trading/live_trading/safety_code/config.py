#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading Bot Configuration
Real market trading configuration - no simulation or test modes
"""

from datetime import time, timedelta, datetime

# Market timing (IST)
MARKET_OPEN = time(13, 23)      # 9:15 AM market open
WINDOW_LENGTH = 3             # Entry window length in minutes (45 minutes)
PREP_START = (datetime.combine(datetime.today(), MARKET_OPEN) - timedelta(seconds=30)).time()  # 30 seconds before market open
ENTRY_TIME = (datetime.combine(datetime.today(), MARKET_OPEN) + timedelta(minutes=WINDOW_LENGTH)).time()  # MARKET_OPEN + WINDOW_LENGTH

# API timing for opening price capture
API_POLL_DELAY_SECONDS = 5     # Poll for opening prices at MARKET_OPEN + 5 seconds
API_RETRY_DELAY_SECONDS = 30   # Retry failed API calls after 30 seconds

# Trading parameters
MAX_POSITIONS = 2              # Maximum concurrent positions
ENTRY_SL_PCT = 0.04            # 4% stop loss below entry
LOW_VIOLATION_PCT = 0.01       # 1% low violation threshold
STRONG_START_GAP_PCT = 0.02    # 2% gap up for Strong Start

# Selection parameters
MAX_STOCKS_TO_SELECT = 2       # Maximum stocks to select for trading
MAX_STOCKS_TO_TRADE = 2        # Maximum stocks to trade
QUALITY_SCORE_THRESHOLD = 15   # Minimum quality score for selection

# Volume validation (SVRO system)
SVRO_MIN_VOLUME_RATIO = 0.05   # 5% minimum relative volume for SVRO
SVRO_VOLUME_BASELINE_DAYS = 20 # Days to calculate volume baseline

# Logging
LOG_LEVEL = 'INFO'             # Logging level
LOG_TO_FILE = True             # Log to file
LOG_TO_CONSOLE = True          # Log to console
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Log format

# Error handling
MAX_RETRIES = 3                # Maximum retry attempts for failed operations
RETRY_DELAY_SECONDS = 5        # Delay between retry attempts

# Market data
WEBSOCKET_RECONNECT_DELAY = 5  # Delay before reconnecting websocket
MAX_WEBSOCKET_RETRIES = 10     # Maximum websocket reconnection attempts

# Paper trading
PAPER_TRADING = True           # Enable paper trading mode
PAPER_TRADING_LOG_FILE = 'paper_trades.csv'  # Paper trading log file
TRADE_LOG_DIR = 'trade_logs'   # Directory for trade logs

print("CONFIG: Real market trading configuration loaded")
print(f"CONFIG: Market open: {MARKET_OPEN}")
print(f"CONFIG: Entry time: {ENTRY_TIME}")
print(f"CONFIG: API poll delay: {API_POLL_DELAY_SECONDS} seconds")
print(f"CONFIG: Max positions: {MAX_POSITIONS}")
print(f"CONFIG: Entry SL: {ENTRY_SL_PCT*100}%")
print(f"CONFIG: Low violation: {LOW_VIOLATION_PCT*100}%")
print(f"CONFIG: Strong start gap: {STRONG_START_GAP_PCT*100}%")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reversal Trading Bot - Clean Modular Orchestrator
Dedicated bot for OOPS reversal trading using official opening prices from API
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz
import psutil
import portalocker
import threading

# Add src to path
sys.path.append('src')

def kill_duplicate_processes():
    """Kill any other instances of reversal bot"""
    try:
        current_pid = os.getpid()
        killed_count = 0

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.name() == 'python' and
                    proc.pid != current_pid and
                    proc.cmdline() and
                    'run_reversal.py' in ' '.join(proc.cmdline())):

                    proc.kill()
                    killed_count += 1
                    print(f"KILLED duplicate reversal bot process {proc.pid}")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed_count > 0:
            print(f"CLEANED up {killed_count} duplicate reversal processes")
            time_module.sleep(2)

    except Exception as e:
        print(f"WARNING: Could not check for duplicates: {e}")

def acquire_singleton_lock():
    """Ensure only one instance of reversal bot runs"""
    lock_file = 'reversal_bot.lock'

    try:
        lock_handle = open(lock_file, 'w')
        portalocker.lock(lock_handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
        globals()['lock_handle'] = lock_handle
        print("[LOCK] Reversal bot singleton lock acquired")

    except portalocker.LockException:
        print("ERROR: Another reversal bot instance is already running - exiting")
        sys.exit(1)
    except Exception as e:
        print(f"WARNING: Could not acquire singleton lock: {e}")

def cleanup_singleton_lock():
    """Clean up the reversal bot singleton lock"""
    try:
        if 'lock_handle' in globals():
            globals()['lock_handle'].close()
            os.remove('reversal_bot.lock')
            print("[UNLOCK] Reversal bot singleton lock released")
    except Exception as e:
        print(f"WARNING: Could not cleanup lock: {e}")

def run_reversal_bot():
    """Run the reversal trading bot using API-based opening prices"""

    print("STARTING REVERSAL TRADING BOT (MODULAR ARCHITECTURE)")
    print("=" * 55)

    # Import components directly
    sys.path.append('src/trading/live_trading')

    from src.trading.live_trading.reversal_stock_monitor import ReversalStockMonitor
    from src.trading.live_trading.reversal_monitor import ReversalMonitor
    from src.trading.live_trading.rule_engine import RuleEngine
    from src.trading.live_trading.selection_engine import SelectionEngine
    from src.trading.live_trading.paper_trader import PaperTrader
    from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer

    from src.utils.upstox_fetcher import UpstoxFetcher
    from config import MARKET_OPEN, ENTRY_TIME, API_POLL_DELAY_SECONDS, API_RETRY_DELAY_SECONDS

    # Create components
    upstox_fetcher = UpstoxFetcher()
    monitor = ReversalStockMonitor()
    reversal_monitor = ReversalMonitor()
    rule_engine = RuleEngine()
    selection_engine = SelectionEngine()
    paper_trader = PaperTrader()

    IST = pytz.timezone('Asia/Kolkata')

    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    # MODULAR: Load reversal stock configuration
    from src.trading.live_trading.stock_classifier import StockClassifier
    classifier = StockClassifier()
    stock_config = classifier.get_reversal_stock_configuration()

    symbols = stock_config['symbols']
    situations = stock_config['situations']

    print(f"LOADED {len(symbols)} reversal stocks")

    # MODULAR: Get previous closes using LTP API
    prev_closes = {}
    for symbol in symbols:
        try:
            data = upstox_fetcher.get_ltp_data(symbol)
            if data and 'cp' in data and data['cp'] is not None:
                prev_closes[symbol] = float(data['cp'])
        except Exception as e:
            print(f"ERROR {symbol}: {e}")

    # MODULAR: Prepare instruments and stocks
    instrument_keys = []
    stock_symbols = {}
    for symbol, prev_close in prev_closes.items():
        try:
            key = upstox_fetcher.get_instrument_key(symbol)
            if key:
                instrument_keys.append(key)
                stock_symbols[key] = symbol
                situation = situations.get(symbol, 'reversal_s2')
                monitor.add_stock(symbol, key, prev_close, situation)
        except Exception as e:
            pass

    print(f"PREPARED {len(instrument_keys)} reversal instruments")

    # MODULAR: Initialize data streamer
    data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)

    print("REVERSAL BOT INITIALIZED - MODULAR ARCHITECTURE")
    print()

    try:
        # MODULAR: PREP PHASE
        print("=== PREP PHASE ===")
        from src.trading.live_trading.stock_scorer import stock_scorer
        stock_scorer.preload_metadata(list(prev_closes.keys()), prev_closes)

        if reversal_monitor.load_watchlist("src/trading/reversal_list.txt"):
            reversal_monitor.rank_stocks_by_quality()

        # MODULAR: Wait for prep start
        from config import PREP_START
        current_time = datetime.now(IST).time()
        if current_time < PREP_START:
            prep_datetime = datetime.combine(datetime.now(IST).date(), PREP_START)
            prep_datetime = IST.localize(prep_datetime)
            current_datetime = datetime.now(IST)
            wait_seconds = (prep_datetime - current_datetime).total_seconds()
            if wait_seconds > 0:
                print(f"WAITING {wait_seconds:.0f} seconds until prep start...")
                time_module.sleep(wait_seconds)

        print("=== TRADING PHASE ===")

        # MODULAR: Connect to data stream
        if not data_streamer.connect():
            print("FAILED to connect data stream")
            return

        print("CONNECTED Data stream connected")

        # MODULAR: Wait for market open
        market_open = MARKET_OPEN
        current_time = datetime.now(IST).time()
        if current_time < market_open:
            market_datetime = datetime.combine(datetime.now(IST).date(), market_open)
            market_datetime = IST.localize(market_datetime)
            current_datetime = datetime.now(IST)
            wait_seconds = (market_datetime - current_datetime).total_seconds()
            if wait_seconds > 0:
                print(f"WAITING {wait_seconds:.0f} seconds for market open...")
                time_module.sleep(wait_seconds)

        print("MARKET OPEN! Waiting 5 seconds for stable data...")
        time_module.sleep(5)  # ⏰ FIXED: 5-second delay

        # MODULAR: Get opening prices and validate gaps
        ohlc_data = upstox_fetcher.get_current_ohlc([stock_symbols[key] for key in instrument_keys])

        opening_prices = {}
        for key in instrument_keys:
            symbol = stock_symbols[key]
            if symbol in ohlc_data and 'open' in ohlc_data[symbol]:
                opening_prices[symbol] = ohlc_data[symbol]['open']

        # MODULAR: Gap validation
        from bot_modules.reversal.reversal_gap_module import validate_gaps_after_opening_prices
        qualified_stocks = validate_gaps_after_opening_prices(monitor.stocks, opening_prices)
        print(f"GAP VALIDATION: {len(qualified_stocks)} stocks qualified")

        # MODULAR: Waiting window monitoring
        from bot_modules.reversal.reversal_waiting_monitor import monitor_waiting_window, prepare_entry_triggers
        monitor_waiting_window(monitor.stocks, data_streamer, ENTRY_TIME)
        prepare_entry_triggers(monitor.stocks)

        # MODULAR: Stock selection
        qualified_stocks = monitor.get_qualified_stocks()
        selected_stocks = selection_engine.select_stocks(qualified_stocks)
        global_selected_symbols = {stock.symbol for stock in selected_stocks}

        print(f"STOCK SELECTION: {len(selected_stocks)} stocks selected")
        for stock in selected_stocks:
            stock.entry_ready = True

        # MODULAR: Live trading execution
        print("=== LIVE TRADING ===")
        from bot_modules.reversal.reversal_trading_engine import execute_reversal_trading_cycle
        execute_reversal_trading_cycle(
            stocks=monitor.stocks,
            data_streamer=data_streamer,
            reversal_monitor=reversal_monitor,
            paper_trader=paper_trader,
            entry_time=ENTRY_TIME,
            global_selected_symbols=global_selected_symbols
        )

    except KeyboardInterrupt:
        print("\nSTOPPED by user")

    # MODULAR: Cleanup
    summary = monitor.get_summary()
    paper_trader.log_session_summary(summary)
    paper_trader.export_trades_csv()
    paper_trader.close()

    print("=== REVERSAL BOT SESSION ENDED ===")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    try:
        kill_duplicate_processes()
        acquire_singleton_lock()
        run_reversal_bot()
    except KeyboardInterrupt:
        print("\nReversal bot interrupted by user")
    except SystemExit:
        print("\nReversal bot exited (another instance running)")
    except Exception as e:
        print(f"\nReversal bot error: {e}")
    finally:
        cleanup_singleton_lock()
        print("Reversal bot shutdown complete")

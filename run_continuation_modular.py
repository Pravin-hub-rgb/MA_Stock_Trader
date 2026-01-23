#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuation Trading Bot - Clean Modular Orchestrator
Dedicated bot for SVRO continuation trading using 1-minute OHLC data
"""

import sys
import os
import time as time_module
from datetime import datetime, time
import pytz
import psutil
import portalocker

# Add src to path
sys.path.append('src')

def kill_duplicate_processes():
    """Kill any other instances of continuation bot"""
    try:
        current_pid = os.getpid()
        killed_count = 0

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.name() == 'python' and
                    proc.pid != current_pid and
                    proc.cmdline() and
                    'run_continuation.py' in ' '.join(proc.cmdline())):

                    proc.kill()
                    killed_count += 1
                    print(f"KILLED duplicate continuation bot process {proc.pid}")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed_count > 0:
            print(f"CLEANED up {killed_count} duplicate continuation processes")
            time_module.sleep(2)

    except Exception as e:
        print(f"WARNING: Could not check for duplicates: {e}")

def acquire_singleton_lock():
    """Ensure only one instance of continuation bot runs"""
    lock_file = 'continuation_bot.lock'

    try:
        lock_handle = open(lock_file, 'w')
        portalocker.lock(lock_handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
        globals()['lock_handle'] = lock_handle
        print("[LOCK] Continuation bot singleton lock acquired")

    except portalocker.LockException:
        print("ERROR: Another continuation bot instance is already running - exiting")
        sys.exit(1)
    except Exception as e:
        print(f"WARNING: Could not acquire singleton lock: {e}")

def cleanup_singleton_lock():
    """Clean up the continuation bot singleton lock"""
    try:
        if 'lock_handle' in globals():
            globals()['lock_handle'].close()
            os.remove('continuation_bot.lock')
            print("[UNLOCK] Continuation bot singleton lock released")
    except Exception as e:
        print(f"WARNING: Could not cleanup lock: {e}")

def run_continuation_bot():
    """Run the continuation trading bot using modular architecture"""

    print("STARTING CONTINUATION TRADING BOT (MODULAR ARCHITECTURE)")
    print("=" * 55)

    # Import components directly
    sys.path.append('src/trading/live_trading')

    from src.trading.live_trading.continuation_stock_monitor import StockMonitor
    from src.trading.live_trading.rule_engine import RuleEngine
    from src.trading.live_trading.selection_engine import SelectionEngine
    from src.trading.live_trading.paper_trader import PaperTrader
    from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer

    from src.trading.live_trading.volume_profile import volume_profile_calculator
    from src.utils.upstox_fetcher import UpstoxFetcher
    from src.trading.live_trading.config import MARKET_OPEN, ENTRY_TIME

    # Create components
    upstox_fetcher = UpstoxFetcher()
    monitor = StockMonitor()
    rule_engine = RuleEngine()
    selection_engine = SelectionEngine()
    paper_trader = PaperTrader()

    IST = pytz.timezone('Asia/Kolkata')

    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    # MODULAR: Load continuation stock configuration
    from src.trading.live_trading.stock_classifier import StockClassifier
    classifier = StockClassifier()
    stock_config = classifier.get_continuation_stock_configuration()

    symbols = stock_config['symbols']
    situations = stock_config['situations']

    print(f"LOADED {len(symbols)} continuation stocks")

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
                situation = situations.get(symbol, 'continuation')
                monitor.add_stock(symbol, key, prev_close, situation)
        except Exception as e:
            pass

    print(f"PREPARED {len(instrument_keys)} continuation instruments")

    # MODULAR: Initialize data streamer
    data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)

    print("CONTINUATION BOT INITIALIZED - MODULAR ARCHITECTURE")
    print()

    try:
        # MODULAR: PREP PHASE - Calculate VAH
        print("=== PREP PHASE ===")
        from bot_modules.continuation.vah_calculation_module import calculate_vah_for_continuation_stocks, save_vah_results_to_file, print_vah_results

        continuation_symbols = [symbol for symbol, situation in situations.items() if situation == 'continuation']
        vah_dict = calculate_vah_for_continuation_stocks(continuation_symbols, volume_profile_calculator)

        # Save and display VAH results
        if save_vah_results_to_file(vah_dict, 'continuation'):
            print("VAH results saved to vah_results.json")

        print_vah_results(vah_dict)

        # MODULAR: Load stock scoring metadata
        from src.trading.live_trading.stock_scorer import stock_scorer
        stock_scorer.preload_metadata(list(prev_closes.keys()), prev_closes)

        # MODULAR: Wait for prep end (9:14:30)
        prep_end = time(9, 14, 30)
        current_time = datetime.now(IST).time()
        if current_time < prep_end:
            prep_datetime = datetime.combine(datetime.now(IST).date(), prep_end)
            prep_datetime = IST.localize(prep_datetime)
            current_datetime = datetime.now(IST)
            wait_seconds = (prep_datetime - current_datetime).total_seconds()
            if wait_seconds > 0:
                print(f"WAITING {wait_seconds:.0f} seconds until prep end...")
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

        print("MARKET OPEN! Monitoring live OHLC data...")

        # MODULAR: Opening price capture (OHLC-based at 9:16)
        print("USING OHLC PROCESSING - Opening prices from 1-min candles at 9:16")
        print("Gap validation at 9:16, final qualification at 9:19")

        # MODULAR: Wait for entry decision time (9:19)
        entry_decision_time = ENTRY_TIME
        current_time = datetime.now(IST).time()
        if current_time < entry_decision_time:
            decision_datetime = datetime.combine(datetime.now(IST).date(), entry_decision_time)
            decision_datetime = IST.localize(decision_datetime)
            current_datetime = datetime.now(IST)
            wait_seconds = (decision_datetime - current_datetime).total_seconds()
            if wait_seconds > 0:
                print(f"\nWAITING {wait_seconds:.0f} seconds until entry decision...")
                time_module.sleep(wait_seconds)

        # MODULAR: Volume validation
        print("\n=== VOLUME VALIDATION ===")
        from bot_modules.continuation.volume_validation_module import validate_volume_requirements, update_volume_validation_status

        validation_results = validate_volume_requirements(monitor.stocks)
        update_volume_validation_status(monitor.stocks, validation_results)

        # MODULAR: Stock selection and qualification
        print("\n=== STOCK QUALIFICATION ===")
        monitor.prepare_entries()
        qualified_stocks = monitor.get_qualified_stocks()
        selected_stocks = selection_engine.select_stocks(qualified_stocks)
        global_selected_symbols = {stock.symbol for stock in selected_stocks}

        print(f"QUALIFIED: {len(qualified_stocks)} stocks")
        print(f"SELECTED: {len(selected_stocks)} stocks")

        for stock in selected_stocks:
            stock.entry_ready = True
            vah = vah_dict.get(stock.symbol)
            vah_str = f"VAH: Rs{vah:.2f}" if vah else "No VAH"
            print(f"READY: {stock.symbol} (Entry: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f}) {vah_str}")

        # MODULAR: Live trading execution
        print("\n=== LIVE TRADING ===")
        print("Monitoring for entry/exit signals...")
        from bot_modules.continuation.continuation_trading_engine import execute_continuation_trading_cycle

        execute_continuation_trading_cycle(
            stocks=monitor.stocks,
            data_streamer=data_streamer,
            vah_dict=vah_dict,
            paper_trader=paper_trader,
            entry_time=ENTRY_TIME
        )

    except KeyboardInterrupt:
        print("\nSTOPPED by user")

    # MODULAR: Cleanup
    summary = monitor.get_summary()
    paper_trader.log_session_summary(summary)
    paper_trader.export_trades_csv()
    paper_trader.close()

    print("=== CONTINUATION BOT SESSION ENDED ===")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    try:
        kill_duplicate_processes()
        acquire_singleton_lock()
        run_continuation_bot()
    except KeyboardInterrupt:
        print("\nContinuation bot interrupted by user")
    except SystemExit:
        print("\nContinuation bot exited (another instance running)")
    except Exception as e:
        print(f"\nContinuation bot error: {e}")
    finally:
        cleanup_singleton_lock()
        print("Continuation bot shutdown complete")

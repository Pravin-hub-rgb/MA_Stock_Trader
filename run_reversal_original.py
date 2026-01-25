#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reversal Trading Bot - API-based Opening Prices
Dedicated bot for OOPS reversal trading using official opening prices from API
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz
import psutil
import portalocker
import schedule
import threading

# Add src to path
sys.path.append('src')

# Configure logging to show detailed VAH calculation info
# Use print statements instead of logging for UI compatibility
# logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

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

    print("STARTING REVERSAL TRADING BOT (API-BASED OPENING PRICES)")
    print("=" * 55)

    # Import components directly
    sys.path.append('src/trading/live_trading')

    from src.trading.live_trading.stock_monitor import StockMonitor
    from src.trading.live_trading.reversal_monitor import ReversalMonitor
    from src.trading.live_trading.rule_engine import RuleEngine
    from src.trading.live_trading.selection_engine import SelectionEngine
    from src.trading.live_trading.paper_trader import PaperTrader
    from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer

    from src.utils.upstox_fetcher import UpstoxFetcher
    from config import MARKET_OPEN, ENTRY_TIME, API_POLL_DELAY_SECONDS, API_RETRY_DELAY_SECONDS

    # Create components
    upstox_fetcher = UpstoxFetcher()
    monitor = StockMonitor()
    reversal_monitor = ReversalMonitor()
    rule_engine = RuleEngine()
    selection_engine = SelectionEngine()
    paper_trader = PaperTrader()

    IST = pytz.timezone('Asia/Kolkata')

    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    # Load reversal stock configuration
    from src.trading.live_trading.stock_classifier import StockClassifier
    classifier = StockClassifier()
    stock_config = classifier.get_reversal_stock_configuration()

    symbols = stock_config['symbols']
    situations = stock_config['situations']

    print(f"LOADED {len(symbols)} reversal stocks:")
    for symbol in symbols:
        situation = situations[symbol]
        desc = {
            'reversal_s1': 'Reversal Uptrend',
            'reversal_s2': 'Reversal Downtrend',
            'reversal_vip': 'VIP Reversal',
            'reversal_tertiary': 'Tertiary Reversal'
        }.get(situation, situation)
        print(f"   {symbol}: {desc}")

    # Get previous closes using LTP API
    prev_closes = {}
    for symbol in symbols:
        try:
            data = upstox_fetcher.get_ltp_data(symbol)
            if data and 'cp' in data and data['cp'] is not None:
                prev_closes[symbol] = float(data['cp'])
                print(f"   OK {symbol}: Rs{prev_closes[symbol]:.2f}")
            else:
                print(f"   ERROR {symbol}: No previous close data")
        except Exception as e:
            print(f"   ERROR {symbol}: {e}")

    # Prepare instruments
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
            print(f"   ERROR {symbol}: No instrument key")

    print(f"\nPREPARED {len(instrument_keys)} reversal instruments")

    # Initialize data streamer
    data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)

    # API Polling for Opening Prices (Expert's Solution)
    api_retry_count = 0
    max_api_retries = 1  # One retry after 3 seconds

    def poll_opening_prices():
        """Get opening prices from Upstox OHLC API with interval=1d for session data"""
        global api_retry_count

        print("POLLING: Getting opening prices from API...")
        print(f"Current time: {datetime.now(IST).strftime('%H:%M:%S')}")
        print(f"Instrument keys: {len(instrument_keys)}")
        
        try:
            # Use the working OHLC API method we tested
            ohlc_data = upstox_fetcher.get_current_ohlc([stock_symbols[key] for key in instrument_keys])
            print(f"API response: {ohlc_data}")
            
            success_count = 0
            
            for key in instrument_keys:
                symbol = stock_symbols[key]
                if symbol in ohlc_data and 'open' in ohlc_data[symbol]:
                    open_price = ohlc_data[symbol]['open']
                    stock = monitor.stocks.get(key)
                    if stock and stock.open_price is None:
                        stock.set_open_price(open_price)
                        stock.validate_gap()
                        success_count += 1
                        print(f"{symbol}: Official open Rs{open_price:.2f} set")
                        # Log opening price for monitoring
                        print(f"OPENING PRICE LOG: {symbol} = Rs{open_price:.2f}")
                
            print(f"API POLL SUCCESS: {success_count}/{len(instrument_keys)} opening prices retrieved")
            
            # Trigger chain reaction for gap validation and qualification
            print("CHAIN REACTION: Starting gap validation and qualification...")
            for stock in monitor.stocks.values():
                if stock.open_price and not stock.gap_validated:
                    stock.validate_gap()
                    print(f"   {stock.symbol}: Gap validation completed")

            # Reset retry count on success
            api_retry_count = 0

        except Exception as e:
            api_retry_count += 1
            print(f"API POLL FAILED (attempt {api_retry_count}): {e}")
            import traceback
            traceback.print_exc()

            # Retry once after 3 seconds if this was the first attempt
            if api_retry_count <= max_api_retries:
                retry_time = datetime.now(IST) + timedelta(seconds=API_RETRY_DELAY_SECONDS)
                print(f"API RETRY: Scheduling retry at {retry_time.strftime('%H:%M:%S')}")

                def retry_poll():
                    poll_opening_prices()

                # Schedule retry
                timer = threading.Timer(API_RETRY_DELAY_SECONDS, retry_poll)
                timer.daemon = True
                timer.start()

    def schedule_api_poll():
        """Schedule API poll for MARKET_OPEN + API_POLL_DELAY_SECONDS"""
        # Calculate poll time: market open + delay
        poll_datetime = datetime.combine(datetime.now(IST).date(), MARKET_OPEN) + timedelta(seconds=API_POLL_DELAY_SECONDS)
        poll_time_str = poll_datetime.strftime("%H:%M:%S")

        print(f"Polling for opening prices at {poll_time_str} (market open + {API_POLL_DELAY_SECONDS}s)")

        # Schedule the poll
        schedule.every().day.at(poll_time_str).do(poll_opening_prices)

        # If we're already past the poll time today, poll immediately
        current_time = datetime.now(IST).time()
        if current_time >= poll_datetime.time():
            print("API SCHEDULER: Poll time already passed, polling immediately")
            poll_opening_prices()
        else:
            print(f"API SCHEDULER: Poll scheduled for {poll_time_str}, waiting...")

    # Schedule API polling
    schedule_api_poll()

    # Reversal tick handler - ticks for monitoring only (opening prices from API)
    def tick_handler_reversal(instrument_key, symbol, price, timestamp, ohlc_list=None):
        """Reversal tick handler - ticks for monitoring/triggers only"""
        global global_selected_stocks, global_selected_symbols

        # LOG ACTUAL TICK PRICE AND TIME (removed to reduce spam)

        monitor.process_tick(instrument_key, symbol, price, timestamp, ohlc_list)

        # Get stock for processing
        stock = monitor.stocks.get(instrument_key)
        if not stock:
            return

        # Process OOPS reversal logic (only if opening price is available from API)
        if stock and stock.situation == 'reversal_s2':
            # Check OOPS reversal conditions
            if reversal_monitor.check_oops_trigger(symbol, stock.open_price, stock.previous_close, price):
                if not stock.oops_triggered:
                    stock.oops_triggered = True
                    print(f"TARGET {symbol}: OOPS reversal triggered - gap down + prev close cross")
                    # Enter position immediately for OOPS
                    stock.entry_high = price
                    stock.entry_sl = price * 0.96  # 4% SL
                    stock.enter_position(price, timestamp)
                    paper_trader.log_entry(stock, price, timestamp)

        # Check violations for opened stocks (continuous monitoring)
        monitor.check_violations()

        # Prepare entries for newly qualified stocks
        qualified_stocks = monitor.get_qualified_stocks()
        for stock in qualified_stocks:
            if not stock.entry_ready:
                # This stock just got qualified, prepare entry levels
                monitor.prepare_entries()  # This will set entry levels for all qualified stocks
                # Re-get qualified stocks to include the newly prepared ones
                qualified_stocks = monitor.get_qualified_stocks()
                global_selected_stocks = selection_engine.select_stocks(qualified_stocks)
                global_selected_symbols = {stock.symbol for stock in global_selected_stocks}

                for sel_stock in global_selected_stocks:
                    if not sel_stock.entry_ready:
                        sel_stock.entry_ready = True
                        gap_pct = ((sel_stock.open_price-sel_stock.previous_close)/sel_stock.previous_close*100)
                        candidate_type = sel_stock.get_candidate_type()
                        print(f"OK {sel_stock.symbol} qualified as {candidate_type} - Gap: {gap_pct:+.1f}% | Entry: Rs{sel_stock.entry_high:.2f} | SL: Rs{sel_stock.entry_sl:.2f}")
                break  # Only do this once per tick to avoid spam

        # Check entry signals only after entry time (only for selected stocks)
        current_time = datetime.now(IST).time()
        if current_time >= ENTRY_TIME and global_selected_stocks:
            entry_signals = monitor.check_entry_signals()

            for stock in entry_signals:
                if stock.symbol in global_selected_symbols:  # Only allow selected stocks to enter
                    print(f"ENTRY {stock.symbol} entry triggered at Rs{price:.2f}, SL placed at Rs{stock.entry_sl:.2f}")
                    stock.enter_position(price, timestamp)
                    paper_trader.log_entry(stock, price, timestamp)

            # Check Strong Start entry signals for reversal_s1
            for stock in monitor.stocks.values():
                if stock.symbol in global_selected_symbols and stock.situation in ['reversal_s1']:
                    # Check Strong Start conditions
                    if reversal_monitor.check_strong_start_trigger(stock.symbol, stock.open_price, stock.previous_close, stock.daily_low):
                        if not stock.strong_start_triggered:
                            stock.strong_start_triggered = True
                            print(f"TARGET {stock.symbol}: Strong Start triggered - gap up + open≈low")
                            # Enter position for Strong Start
                            stock.entry_high = price
                            stock.entry_sl = price * 0.96  # 4% SL
                            stock.enter_position(price, timestamp)
                            paper_trader.log_entry(stock, price, timestamp)

        # Check trailing stops and exit signals for entered positions
        if current_time >= ENTRY_TIME:
            # Check for trailing stop adjustments (5% profit -> move SL to entry)
            for stock in monitor.stocks.values():
                if stock.entered and stock.entry_price and stock.current_price:
                    profit_pct = (stock.current_price - stock.entry_price) / stock.entry_price
                    if profit_pct >= 0.05:  # 5% profit
                        new_sl = stock.entry_price  # Move SL to breakeven
                        if stock.entry_sl < new_sl:
                            old_sl = stock.entry_sl
                            stock.entry_sl = new_sl
                            print(f"TRAILING {stock.symbol} trailing stop adjusted: Rs{old_sl:.2f} -> Rs{new_sl:.2f} (5% profit)")

            # Check exit signals (including updated trailing stops)
            exit_signals = monitor.check_exit_signals()
            for stock in exit_signals:
                pnl = (price - stock.entry_price) / stock.entry_price * 100
                print(f"EXIT {stock.symbol} exited at Rs{price:.2f}, PNL: {pnl:+.2f}%")
                stock.exit_position(price, timestamp, "Stop Loss Hit")
                paper_trader.log_exit(stock, price, timestamp, "Stop Loss Hit")

        # Position status logging removed to reduce tick spam

    # Set the reversal tick handler
    data_streamer.tick_handler = tick_handler_reversal
    global_selected_stocks = []
    global_selected_symbols = set()

    print("\n=== REVERSAL BOT INITIALIZED ===")
    print("Using API-based opening prices with tick monitoring")
    print()

    try:
        # PREP TIME: Load metadata and prepare data
        print("=== PREP TIME: Loading metadata and preparing data ===")

        # Load stock scoring metadata (ADR, volume baselines, etc.)
        from src.trading.live_trading.stock_scorer import stock_scorer
        stock_scorer.preload_metadata(list(prev_closes.keys()), prev_closes)
        print("OK Stock metadata loaded for scoring")

        # Load reversal watchlist
        reversal_list_path = "src/trading/reversal_list.txt"
        if reversal_monitor.load_watchlist(reversal_list_path):
            print("OK Reversal watchlist loaded")
            reversal_monitor.rank_stocks_by_quality()
        else:
            print("WARNING: Could not load reversal watchlist")

        # Wait for prep end (market open - 30 seconds)
        from config import PREP_END
        current_time = datetime.now(IST).time()

        if current_time < PREP_END:
            prep_datetime = datetime.combine(datetime.now(IST).date(), PREP_END)
            prep_datetime = IST.localize(prep_datetime)
            current_datetime = datetime.now(IST)
            wait_seconds = (prep_datetime - current_datetime).total_seconds()
            if wait_seconds > 0:
                print(f"WAITING {wait_seconds:.0f} seconds until prep end...")
                time_module.sleep(wait_seconds)

        print("=== STARTING REVERSAL TRADING PHASE ===")

        # Connect to data stream
        print("ATTEMPTING to connect to data stream...")
        if data_streamer.connect():
            print("CONNECTED Data stream connected")

            # Wait for market open
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

            print("MARKET OPEN! Monitoring live tick data...")

            # For reversal: API-based opening price capture
            print("USING API-BASED OPENING PRICE CAPTURE")
            print("Official opening prices from exchange at market open + 5 seconds")

            # Continue with normal entry timing
            entry_time = ENTRY_TIME
            current_time = datetime.now(IST).time()

            if current_time < entry_time:
                entry_datetime = datetime.combine(datetime.now(IST).date(), entry_time)
                entry_datetime = IST.localize(entry_datetime)
                current_datetime = datetime.now(IST)
                wait_seconds = (entry_datetime - current_datetime).total_seconds()
                if wait_seconds > 0:
                    print(f"\nWAITING {wait_seconds:.0f} seconds until entry time...")
                    time_module.sleep(wait_seconds)

            # Prepare entries and select stocks
            print("\n=== PREPARING ENTRIES ===")

            # Show current status after reversal qualification
            print("POST-REVERSAL QUALIFICATION STATUS:")
            for stock in monitor.stocks.values():
                open_status = f"Open: Rs{stock.open_price:.2f}" if stock.open_price else "No opening price"

                gap_pct = 0.0
                if stock.open_price and stock.previous_close:
                    gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close) * 100

                gap_status = "Gap validated" if stock.gap_validated else f"Gap: {gap_pct:+.1f}%"
                low_status = "Low checked" if stock.low_violation_checked else "Low not checked"

                situation_desc = {
                    'reversal_s1': 'Rev-U',
                    'reversal_s2': 'Rev-D',
                    'reversal_vip': 'VIP',
                    'reversal_tertiary': 'Tert'
                }.get(stock.situation, stock.situation)

                rejection_info = ""
                if stock.rejection_reason:
                    rejection_info = f" | REJECTED: {stock.rejection_reason}"

                print(f"   {stock.symbol} ({situation_desc}): {open_status} | {gap_status} | {low_status}{rejection_info}")

            monitor.prepare_entries()

            qualified_stocks = monitor.get_qualified_stocks()
            print(f"Qualified stocks: {len(qualified_stocks)}")

            selected_stocks = selection_engine.select_stocks(qualified_stocks)
            print(f"Selected stocks: {[s.symbol for s in selected_stocks]}")

            # Mark selected stocks as ready
            for stock in selected_stocks:
                stock.entry_ready = True
                print(f"READY to trade: {stock.symbol} (Entry: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f})")

            # Initialize selected_stocks for the tick handler
            global_selected_symbols = {stock.symbol for stock in selected_stocks}

            # Keep monitoring for entries, exits, and trailing stops
            print("\nMONITORING for entry/exit signals...")

            # Start scheduler for API polling in background thread
            def run_scheduler():
                while True:
                    schedule.run_pending()
                    time_module.sleep(1)

            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            print("SCHEDULER: Background API polling thread started")

            data_streamer.run()

        else:
            print("FAILED to connect data stream")
            print("CONTINUING without data stream for testing...")

    except KeyboardInterrupt:
        print("\nSTOPPED by user")

    # Cleanup
    print("\n=== CLEANUP ===")
    summary = monitor.get_summary()
    paper_trader.log_session_summary(summary)
    paper_trader.export_trades_csv()
    paper_trader.close()

    print("=== REVERSAL BOT SESSION ENDED ===")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    try:
        # Prevent multiple instances
        kill_duplicate_processes()
        acquire_singleton_lock()

        # Run the reversal bot
        run_reversal_bot()

    except KeyboardInterrupt:
        print("\nReversal bot interrupted by user")
    except SystemExit:
        print("\nReversal bot exited (another instance running)")
    except Exception as e:
        print(f"\nReversal bot error: {e}")
    finally:
        # Always cleanup
        cleanup_singleton_lock()
        print("Reversal bot shutdown complete")
